import asyncio
import threading
import customtkinter as ctk
from launcher import Launcher
from pipeline import Pipeline


class AIWindow:
    def __init__(self):
        self._queue_launcher = asyncio.Queue()
        self._queue_pipeline = asyncio.Queue()
        self._launcher = Launcher(queue_launcher=self._queue_launcher)
        self._pipeline = Pipeline(queue_dialog=self._queue_pipeline)
        self._button: ctk.CTkButton | None = None
        self._indicator_frame: ctk.CTkFrame | None = None
        self._text_area: ctk.CTkTextbox | None = None

    async def observer(self):
        self._text_area.tag_config('ai', foreground="#10B981")
        self._text_area.tag_config('user', foreground="white")
        while True:
            try:
                res = await asyncio.wait_for(self._queue_pipeline.get(), 0.5)
                if res is None:
                    break
                # сборка и обработка сообщений для терминальной версии
                role = res.get("role")
                row = f'{res.get("text")}'
                if role == 'user':
                    row = f"\n{row}\n"
                tag = 'user' if role == 'user' else 'ai'
                self._text_area.after(0, lambda r=row: self._text_area.insert('end', f" {r}", tag))
                self._text_area.after(0, lambda: self._text_area.see('end'))  # noqa

            except asyncio.TimeoutError:
                pass

    async def observer_launcher(self):
        self._text_area.tag_config('tag', foreground="yellow")
        while True:
            try:
                res = await asyncio.wait_for(self._queue_launcher.get(), 0.5)
                if res is None:
                    break
                self._text_area.after(0, lambda r=res: self._text_area.insert('end', f"\n{r['msg']}", 'tag'))
                self._text_area.after(0, lambda: self._text_area.see('end'))  # noqa
            except asyncio.TimeoutError:
                pass

    async def run(self):
        observer_launch = asyncio.create_task(self.observer_launcher())  # запуск наблюдателя за процессом сервера
        observer = asyncio.create_task(self.observer())
        # кнопка переведена в режим stop
        self._button.after(0, self._button.configure(command=lambda: self.stop_assistant()))  # noqa
        self._button.after(0, self._button.configure(text='stop'))  # noqa
        self._indicator_frame.after(0, self._indicator_frame.configure(border_color='gold2'))  # noqa
        await self._launcher.start()
        await self._pipeline.start(services=self._launcher.run_services)
        self._indicator_frame.after(0, self._indicator_frame.configure(border_color='steelblue'))  # noqa
        await observer_launch

    async def stop_stop(self):
        self._indicator_frame.after(0, self._indicator_frame.configure(border_color='gold2'))  # noqa
        await self._pipeline.stop()
        await self._launcher.stop()
        self._indicator_frame.after(0, self._indicator_frame.configure(border_color='gray20'))  # noqa
        self._button.configure(
            text='start',
            command=lambda: threading.Thread(target=lambda: asyncio.run(self.run()), daemon=True).start(),
        )

    def stop_assistant(self):
        threading.Thread(target=asyncio.run(self.stop_stop())).start()

    def window(self, _root, frame, _row_state, _storage):
        frame_left = ctk.CTkFrame(frame, fg_color='transparent', border_width=0)
        self._indicator_frame = ctk.CTkFrame(frame_left)
        self._indicator_frame.configure(
            fg_color='transparent', border_width=20, border_color='gray20', corner_radius=1000,
        )
        self._indicator_frame.pack(expand=True, padx=10, pady=0, anchor='n')
        self._button = ctk.CTkButton(
            frame_left, text='start',
            command=lambda: threading.Thread(target=lambda: asyncio.run(self.run()), daemon=True).start(),
        )
        self._button.pack(expand=True, fill='x', padx=10, pady=0, anchor='s')
        frame_left.pack(expand=False, fill='both', side='left', padx=10, pady=10)
        # виджеты
        _row_state.configure(text='диалог с ai', text_color='gold3')
        frame_right = ctk.CTkFrame(frame)
        self._text_area = ctk.CTkTextbox(frame_right, width=550)
        self._text_area.pack(expand=True, fill='both', padx=10, pady=10)
        frame_right.pack(expand=True, fill='both', side='right', padx=10, pady=10)
