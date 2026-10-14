from gui.root import MainWindowUi
from gui.ai_window import AIWindow
from gui.settings_window import SettingsWindow

ai_window = AIWindow()  # главное окно для диалога с ИИ
settings_window = SettingsWindow()  # настройки

# инициализация root
main_window = MainWindowUi(
    pages={
        'ai_window': ai_window.window,
        'settings_window': settings_window.window,
    },
    min_width=850, min_height=500,
    resizable_width=True, resizable_height=True,
    footer=True, header=True, header_text='AI ассистент', nav_theme_switcher=True,
    nav_pages_combobox=True, nav_pages_buttons=True,
)
main_window.root.iconbitmap('icon.ico')
main_window.set_page('ai_window')
main_window.start()
