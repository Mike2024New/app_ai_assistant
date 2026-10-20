import asyncio
import os
import threading

import customtkinter as ctk
import psutil

from settings_editor import SettingsEditor
from metric import monitor


class MonitorWindow:
    def __init__(self):
        self._settings = SettingsEditor()

        self._root: ctk.CTk | None = None
        self._frame: ctk.CTkFrame | None = None
        self._row_state: ctk.CTkLabel | None = None
        self._storage: dict | None = None
        self._text_area_monitor: ctk.CTkTextbox | None = None
        self._padx, self._pady = 10, 10

    @staticmethod
    def get_pid_info(pid: int, interval=1):
        p = psutil.Process(pid)

        raw_cpu = p.cpu_percent(interval=interval)
        normalized_cpu = round(raw_cpu / psutil.cpu_count(logical=True), 1)  # нормализация cpu к 100% иначе будет 1000%

        try:
            return {
                'cpu': normalized_cpu,
                'ram': round(p.memory_info().rss / 1024 / 1024 ** 2, 1)
            }
        except psutil.NoSuchProcess:
            return {
                'cpu': 0,
                'ram': 0
            }

    def monitor(self):
        async def monitor_worker():
            while True:
                services = self._storage['services']
                text = f'{"":<10}  {"CPU %":>6}   {"RAM GB":>6}\n'
                tasks = []
                services_list = list(services.keys())
                for srv, params in services.items():
                    task = asyncio.create_task(asyncio.to_thread(lambda p=params: self.get_pid_info(pid=p['pid'])))
                    tasks.append(task)

                # замеры для текущего приложения
                services_list.append('app')
                tasks.append(
                    asyncio.create_task(asyncio.to_thread(lambda: self.get_pid_info(pid=os.getpid())))
                )

                result = await asyncio.gather(*tasks, return_exceptions=True)
                cpu_total, ram_total = 0, 0

                for task, srv, r in zip(tasks, services_list, result):
                    if isinstance(r, Exception):
                        cpu, ram = 0, 0
                    else:
                        cpu, ram = r['cpu'], r['ram']
                    cpu_total += cpu
                    ram_total += ram
                    info = f'{srv:<10}  {cpu:>6}  {ram:>6}'
                    # info = f'{srv} : cpu {cpu} % | ram {ram} GB'
                    text += f'{info}\n'

                cpu_total = round(cpu_total, 1)
                ram_total = round(ram_total, 1)
                text += f'{"total":<10}  {cpu_total:>6}  {ram_total:>6}'
                # text += f'total : cpu {cpu_total} % | ram {ram_total} GB'
                self._text_area_monitor.delete('1.0', 'end')
                self._text_area_monitor.insert('1.0', text)
                await asyncio.sleep(0.1)

        asyncio.run(monitor_worker())

    def window(self, root: ctk.CTk, frame: ctk.CTkFrame, row_state: ctk.CTkLabel, storage: dict):

        self._root = root
        self._frame = frame
        self._row_state = row_state
        self._storage = storage
        body_header_label = ctk.CTkLabel(frame, text='Монитор')
        body_header_label.configure(font=('Consolas', 18, 'bold'))
        body_header_label.pack(expand=False, side='top', anchor='nw', padx=10, pady=(self._padx / 2, self._pady / 2))

        # блок текущий монитор
        self._text_area_monitor = ctk.CTkTextbox(frame, width=550, height=120, fg_color='transparent')
        self._text_area_monitor.configure(font=('Consolas', 16, 'normal'), spacing1=1, spacing3=1)
        self._text_area_monitor.pack(expand=True, fill='both', padx=10, pady=5)

        # блок для вывода информации о ресурсах ПК
        text_area = ctk.CTkTextbox(frame, width=550, fg_color='transparent')
        text_area.configure(font=('roboto', 14, 'normal'))
        text_area.pack(expand=True, fill='both', padx=10, pady=10)

        def callback():
            if not 'services' in self._storage:
                return
            info = monitor()
            text_area.delete('1.0', 'end')
            text_area.insert('1.0', info)
            threading.Thread(target=self.monitor, daemon=True).start()
            btn.configure(state='disabled')

        btn = ctk.CTkButton(frame, text='start', cursor='hand2')
        btn.configure(command=lambda: callback())
        btn.pack(expand=False, padx=10, pady=10, anchor='ne')
