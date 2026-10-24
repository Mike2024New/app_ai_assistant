import sys
from pathlib import Path

# Если передан флаг --run-script, выполнить скрипт и выйти (выполнение пользовательских скриптов)
if '--run-script' in sys.argv:
    idx = sys.argv.index('--run-script')
    script_path = Path(sys.argv[idx + 1])
    script_args = sys.argv[idx + 2:]
    sys.argv = [str(script_path)] + script_args

    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8')

    # ФИКС: Перенаправить stdout в stderr.
    # PyInstaller (--noconsole) часто ломает stdout, но stderr работает.
    # subprocess.run(capture_output=True) будет читать stderr.
    sys.stdout = sys.stderr

    # чтение файла с кодом для получения результата
    with open(script_path, 'r', encoding='utf-8') as f:
        code = f.read()
    try:
        exec(code, {'__name__': '__main__', '__file__': str(script_path)})
    finally:
        sys.stdout.flush()

    sys.exit(0)

# запуск программы в обычном режиме
else:
    import asyncio
    import threading

    from gui.root import MainWindowUi
    from gui.ai_window import AIWindow
    from gui.settings_window import SettingsWindow
    from gui.monitor_window import MonitorWindow
    from gui.scripts_window import ScriptsWindow
    from gui.download_assets_window import AdditionallyWindow
    from infrastructure_path_utils import get_root_dir_path
    from config import logger

    event = asyncio.Event()

    feedback_dict = {}  # процесс загрузок

    ai_window = AIWindow()  # главное окно для диалога с ИИ
    settings_window = SettingsWindow()  # настройки
    monitor_window = MonitorWindow()
    scripts_window = ScriptsWindow()
    addition_window = AdditionallyWindow(event=event, feedback_dict=feedback_dict)
    addition_window.start()  # продолжение загрузок если были

    # инициализация root
    main_window = MainWindowUi(
        pages={
            'ai_window': ai_window.window,
            'settings_window': settings_window.window,
            'scripts_window': scripts_window.window,
            'monitor_window': monitor_window.window,
            'addition_window': addition_window.window,
        },
        min_width=1050, min_height=650,
        resizable_width=True, resizable_height=True,
        footer=True, header=True, header_text='AI ассистент', nav_theme_switcher=True,
        nav_pages_combobox=True, nav_pages_buttons=True,
    )


    @logger.catch
    def root_protocol():
        # остановка сервисов (выход при наж. на закрыть)
        def stop_worker():
            try:
                asyncio.run(ai_window.stop())  # метод идемпотентен (флаг is_running)
                addition_window.finish()  # сохранить не докачанные загрузки
                event.set()  # сброс event для окон с обсервацией
            except Exception as err:
                logger.error(f'Ошибка при остановке потока {err}')
            finally:
                main_window.root.after(0, main_window.root.destroy)

        threading.Thread(target=stop_worker, daemon=True).start()


    main_window.root.protocol("WM_DELETE_WINDOW", lambda: root_protocol())

    main_window.root.iconbitmap(get_root_dir_path() / 'icon.ico')
    main_window.set_page('ai_window')
    main_window.start()
    # погасить все дочерние циклы
    event.set()
