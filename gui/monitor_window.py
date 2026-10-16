import customtkinter as ctk
from settings_editor import SettingsEditor
from metric import monitor


class MonitorWindow:
    def __init__(self):
        self._settings = SettingsEditor()

        self._root: ctk.CTk | None = None
        self._frame: ctk.CTkFrame | None = None
        self._row_state: ctk.CTkLabel | None = None
        self._storage: dict | None = None
        self._padx, self._pady = 10, 10

    def window(self, root: ctk.CTk, frame: ctk.CTkFrame, row_state: ctk.CTkLabel, storage: dict):
        self._root = root
        self._frame = frame
        self._row_state = row_state
        self._storage = storage
        body_header_label = ctk.CTkLabel(frame, text='Монитор')
        body_header_label.configure(font=('roboto', 18, 'bold'))
        body_header_label.pack(side='top', anchor='nw', padx=10, pady=(self._padx / 2, self._pady / 2))
        text_area = ctk.CTkTextbox(frame, width=550)
        text_area.pack(expand=True, fill='both', padx=10, pady=10)
        btn = ctk.CTkButton(frame, text='Отчет',cursor='hand2')

        def callback():
            info = monitor()
            text_area.delete('1.0', 'end')
            text_area.insert('1.0', info)

        btn.configure(command=lambda: callback())
        btn.pack(expand=False, padx=10, pady=10)
