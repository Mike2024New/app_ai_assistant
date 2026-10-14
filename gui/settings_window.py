import customtkinter as ctk


class SettingsWindow:
    def __init__(self):
        pass

    def window(self, _root: ctk.CTk, frame: ctk.CTkFrame, _row_state: ctk.CTkLabel, _storage: dict):
        body_header_label = ctk.CTkLabel(frame, text='Настройки')
        body_header_label.configure(font=('roboto', 18, 'bold'))
        body_header_label.pack(side='top', anchor='nw', padx=10, pady=(5, 5))
        lbl = ctk.CTkLabel(frame, text='example')
        lbl.pack()
