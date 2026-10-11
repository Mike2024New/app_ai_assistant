from gui.root import MainWindowUi
from gui.ai_window import AIWindow

ai_window = AIWindow()

main_window = MainWindowUi(
    pages={
        'ai_window': ai_window.window,
    },
    min_width=350, min_height=500,
    resizable_width=True, resizable_height=True,
    footer=True, header=True, header_text='AI ассистент', nav_theme_switcher=True,
)
main_window.set_page('ai_window')
main_window.start()
