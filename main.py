import sys
from pathlib import Path

# запуск в режиме "интерпретатора", для выполнения скриптов (executable)
# Если передан флаг --run-script, выполнить скрипт и выйти
if '--run-script' in sys.argv:
    idx = sys.argv.index('--run-script')
    script_path = Path(sys.argv[idx + 1])
    script_args = sys.argv[idx + 2:]
    sys.argv = [str(script_path)] + script_args  # чтобы скрипт видел свои аргументы
    with open(script_path, 'r', encoding='utf-8') as f:
        code = f.read()
    exec(code, {'__name__': '__main__', '__file__': str(script_path)})
    sys.exit(0)

# запуск программы в обычном режиме
else:
    import asyncio
    import threading

    from gui.root import MainWindowUi
    from gui.ai_window import AIWindow
    from gui.settings_window import SettingsWindow
    from gui.monitor_window import MonitorWindow
    from infrastructure_path_utils import get_root_dir_path
    from config import logger

    ai_window = AIWindow()  # главное окно для диалога с ИИ
    settings_window = SettingsWindow()  # настройки
    monitor_window = MonitorWindow()

    # инициализация root
    main_window = MainWindowUi(
        pages={
            'ai_window': ai_window.window,
            'settings_window': settings_window.window,
            'monitor_window': monitor_window.window,
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
            except Exception as err:
                logger.error(f'Ошибка при остановке потока {err}')
            finally:
                main_window.root.after(0, main_window.root.destroy)

        threading.Thread(target=stop_worker, daemon=True).start()


    main_window.root.protocol("WM_DELETE_WINDOW", lambda: root_protocol())

    main_window.root.iconbitmap(get_root_dir_path() / 'icon.ico')
    main_window.set_page('ai_window')
    main_window.start()
