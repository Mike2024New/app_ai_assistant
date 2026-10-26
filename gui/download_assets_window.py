import asyncio
import json
import threading
import hashlib
from time import sleep
import customtkinter as ctk
from config import SettingsEditor
from infrastructure_path_utils import get_root_dir_path
from config import logger
from CTkToolTip import CTkToolTip
from gui.downloader import download_file
from pathlib import Path

window_name = 'addition_window'


class AdditionallyWindow:
    def __init__(self, event: asyncio.Event, feedback_dict: dict | None = None):
        self._settings = SettingsEditor()
        self._event = event
        self._root: ctk.CTk | None = None
        self._frame: ctk.CTkFrame | None = None
        self._row_state: ctk.CTkLabel | None = None
        self._storage: dict | None = None
        self._padx, self._pady = 10, 10
        self._additionaly = {'additionally': []}
        self._feedback_dict = feedback_dict or {}
        self._events_dict = {}
        self._progress_labels = {}
        self._progress_btns = {}

    def start(self):
        print(f'Продолжение загрузок если есть')
        try:
            with open(file=get_root_dir_path() / 'additionally.json', mode='r', encoding='utf-8') as f:
                self._additionaly = json.loads(f.read())
                self._additionaly = self._additionaly['additionally']
        except Exception as err:
            logger.error(f'Не удалось прочитать файл с дополнительными материалами: {err}')

        for add in self._additionaly:
            self._events_dict[add['label']] = asyncio.Event()
            if add['continue']:
                threading.Thread(
                    target=lambda: asyncio.run(
                        download_file(
                            addon=add,
                            event=self._events_dict[add['label']],
                            feedback_dict=self._feedback_dict,
                        )
                    ), daemon=True).start()

    def finish(self):
        print(f'Завершаю загрузки если есть')
        # нужно сохранить информацию о прерванных загрузках, если такие были, чтобы потом продолжить с того же места
        for add in self._additionaly:
            if add['label'] in self._feedback_dict:
                add['continue'] = True
            else:
                add['continue'] = False
        additionally = {'additionally': self._additionaly}
        with open(file=get_root_dir_path() / 'additionally.json', mode='w', encoding='utf-8') as f:
            f.write(json.dumps(additionally, ensure_ascii=False, indent=2))

    @staticmethod
    def calculate_sha256(file_path: Path) -> str:
        sha256_hash = hashlib.sha256()
        # Читаем файл кусками по 64 КБ
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(65536), b""):
                sha256_hash.update(byte_block)  # noqa
        return sha256_hash.hexdigest()

    def window(self, root: ctk.CTk, frame: ctk.CTkFrame, row_state: ctk.CTkLabel, storage: dict):
        self._root = root
        self._frame = frame
        self._row_state = row_state
        self._storage = storage
        body_header_label = ctk.CTkLabel(frame, text='Дополнительно')
        body_header_label.configure(font=('Consolas', 18, 'bold'))
        body_header_label.pack(expand=False, side='top', anchor='nw', padx=10, pady=(self._padx / 2, self._pady / 2))
        scrolable_frame = ctk.CTkScrollableFrame(frame, fg_color='transparent')
        scrolable_frame.pack(expand=True, fill='both', padx=5, pady=5)

        threading.Thread(target=lambda: self.observer(), daemon=True).start()

        for i, addon in enumerate(self._additionaly):
            # file_path = get_root_dir_path().parent / addon['relative_path_file']
            # sha256_file = self.calculate_sha256(file_path=file_path)
            # if sha256_file == addon['sha256']:
            #     continue

            frame_in = ctk.CTkFrame(scrolable_frame, fg_color='transparent')
            frame_in.pack(expand=False, fill='x', padx=10, pady=2, anchor='ne')

            # нумерация строк
            num_label = ctk.CTkLabel(frame_in, text=f'{i}', text_color='tomato', font=('roboto', 14, 'bold'), width=20)
            num_label.pack(expand=False, side='left', padx=10, pady=10)

            # название дополнения
            model_name_label = ctk.CTkLabel(frame_in, text=f'{addon["label"]}', font=('roboto', 14, 'bold'), width=20)
            CTkToolTip(model_name_label, message=addon["description"], delay=0.5, wraplength=250)
            model_name_label.pack(expand=False, side='left', padx=10, pady=10)

            # перейти на страницу источника
            dwnload_btn = ctk.CTkButton(frame_in, cursor='hand2')
            CTkToolTip(dwnload_btn, message=f'Источник: {addon["source"]}', delay=0.5, wraplength=250)
            dwnload_btn.pack(expand=False, side='right', padx=10, pady=10)

            # progress_label
            progress_label = ctk.CTkLabel(frame_in, text=f'', text_color='gold4', width=20)  # формат download 11.2 %
            progress_label.configure(font=('roboto', 14, 'bold'))
            progress_label.pack(expand=False, side='right', padx=10, pady=10)
            self._progress_labels[addon['label']] = progress_label
            self._progress_btns[addon['label']] = dwnload_btn

            if addon['label'] in self._feedback_dict:
                dwnload_btn.configure(text='прервать')
                dwnload_btn.configure(fg_color='red4', hover_color='red1')
            else:
                dwnload_btn.configure(text='загрузить')
                dwnload_btn.configure(fg_color='#10B981', hover_color="#059669")

            dwnload_btn.configure(
                command=lambda add=addon, btn=dwnload_btn: self.download_btn_callback(add=add, btn=btn)
            )

    def download_btn_callback(self, add, btn):
        """Переключатель: если качается — останавить, если нет — начать."""
        # Проверить, идет ли загрузка (есть ли метка в feedback_dict)
        if add['label'] in self._feedback_dict:
            self.stop_download(add, btn)
        else:
            self.start_download(add, btn)

    def start_download(self, add, btn):
        """Запуск загрузки"""
        btn.configure(text='прервать', fg_color='red4', hover_color='red1')
        btn.configure(command=lambda: self.download_btn_callback(add=add, btn=btn))
        threading.Thread(
            target=lambda: asyncio.run(
                download_file(
                    addon=add,
                    event=self._events_dict[add['label']],
                    feedback_dict=self._feedback_dict,
                )
            ), daemon=True).start()

    def stop_download(self, add, btn):
        """Остановка загрузки"""
        btn.configure(text='загрузить', fg_color='#10B981', hover_color="#059669")
        btn.configure(command=lambda: self.download_btn_callback(add=add, btn=btn))

        # Дать сигнал на остановку и удалить из feedback_dict (чтобы она не попала в загрузку при следующем открытии)
        self._events_dict[add['label']].set()
        self._feedback_dict.pop(add['label'], None)
        self.finish()

    def observer(self):
        """Наблюдение за процессом установки"""
        print(f'Запуск')
        while not self._event.is_set():
            sleep(0.2)
            for lbl in self._feedback_dict:
                if lbl not in self._progress_labels:
                    continue
                percent = self._feedback_dict[lbl]['progress']
                if percent < 100:
                    self._progress_labels[lbl].configure(text=f"Загрузка: {percent} %", text_color='gold4')
                else:
                    self._progress_btns[lbl].configure(text='завершено', fg_color='#10B981', hover_color="#059669")
                    self._progress_labels[lbl].configure(text=f"Загрузка: {percent} %", text_color='green')
