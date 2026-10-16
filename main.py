from gui.root import MainWindowUi
from gui.ai_window import AIWindow
from gui.settings_window import SettingsWindow
from gui.monitor_window import MonitorWindow
from infrastructure_path_utils import get_root_dir_path

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

# # В следующей версии нужно будет доделать. Остановку запущенных процессов при нажатии крестика
# def root_protocol():
#     # остановка сервисов
#     main_window.root.after(
#         0,
#         lambda: threading.Thread(target=asyncio.run, args=(ai_window.stop(),), daemon=True).start()
#     )
#     main_window.root.destroy()
#
# main_window.root.protocol("WM_DELETE_WINDOW", lambda: root_protocol())


main_window.root.iconbitmap(get_root_dir_path() / 'icon.ico')
main_window.set_page('ai_window')
main_window.start()
