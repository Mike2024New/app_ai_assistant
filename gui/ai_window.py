import asyncio
import threading
import customtkinter as ctk
from launcher import Launcher
from pipeline import Pipeline


class AIWindow:
    def __init__(self):
        self._running = False
        self._launcher: Launcher | None = None
        self._pipeline: Pipeline | None = None
        self._button: ctk.CTkButton | None = None
        self._indicator_frame: ctk.CTkFrame | None = None
        self._text_area: ctk.CTkTextbox | None = None

    def pipeline_callback(self, res):
        """
        Обработка полученных сообщений. Текст распознанный stt (user) и текст от llm (ai)
        """
        if self._text_area is None:
            return

        role = res.get("role")
        row = f'{res.get("text")}'
        if role == 'user':
            row = f"\n{row}\n"
        tag = 'user' if role == 'user' else 'ai'
        self._text_area.after(0, lambda r=row: self._text_area.insert('end', f" {r}", tag))  # noqa
        self._text_area.after(0, lambda: self._text_area.see('end'))  # noqa

    def launcher_callback(self, res):
        """Запуск сервера, отрисовка прогресса в text_area"""
        if self._text_area is None:
            return
        self._text_area.after(0, lambda r=res: self._text_area.insert('end', f"\n{r['msg']}", ))
        self._text_area.after(0, lambda: self._text_area.see('end'))  # noqa

    async def start(self):
        """Запуск AI ассистента: подъём сервисов launcher -> запуск pypline стримов с сервисами"""
        # конфигурация кнопки переведенной в состояние остановки (подготовка к stop)
        if self._running:
            return
        self._running = True
        self._launcher = Launcher()
        self._pipeline = Pipeline()

        self._button.after(
            0, lambda: self._button.configure(
                text='stop',
                command=lambda: threading.Thread(target=asyncio.run, args=(self.stop(),), daemon=True).start(),
            )
        )  # noqa
        self._indicator_frame.after(0, lambda: self._indicator_frame.configure(border_color='gold2'))  # noqa
        observer_launcher_task = asyncio.create_task(self._launcher.observer(self.launcher_callback))
        await self._launcher.start()
        await self._pipeline.start(services=self._launcher.run_services)
        observer_pipeline_task = asyncio.create_task(self._pipeline.observer(self.pipeline_callback))
        self._indicator_frame.after(0, lambda: self._indicator_frame.configure(border_color='steelblue'))  # noqa
        await observer_pipeline_task
        await observer_launcher_task

    async def stop(self):
        if not self._running:
            return

        self._indicator_frame.after(0, lambda: self._indicator_frame.configure(border_color='gold2'))  # noqa
        await self._pipeline.stop()
        await self._launcher.stop()

        self._indicator_frame.after(0, lambda: self._indicator_frame.configure(border_color='gray18'))  # noqa
        # перевести кнопку обратно в режим start
        self._button.after(
            0, lambda: self._button.configure(
                text='start',
                command=lambda: threading.Thread(target=asyncio.run, args=(self.start(),), daemon=True).start(),
            )
        )
        self._launcher = None
        self._pipeline = None
        self._running = False

    def window(self, _root: ctk.CTk, frame: ctk.CTkFrame, row_state: ctk.CTkLabel, _storage: dict):
        """Основной метод окна, вход в ai ассистента."""
        frame_left = ctk.CTkFrame(frame, fg_color='transparent', border_width=0)
        self._indicator_frame = ctk.CTkFrame(frame_left)
        self._indicator_frame.configure(
            fg_color='transparent', border_width=20, border_color='gray18', corner_radius=1000,
        )
        self._indicator_frame.pack(expand=True, padx=10, pady=0, anchor='n')
        # запуск диалога с llm (активация при нажатии кнопки)
        self._button = ctk.CTkButton(
            frame_left, text='start',
            command=lambda: threading.Thread(target=asyncio.run, args=(self.start(),), daemon=True).start()
        )
        self._button.pack(expand=True, fill='x', padx=10, pady=0, anchor='s')
        frame_left.pack(expand=False, fill='both', side='left', padx=10, pady=10)
        # виджеты
        row_state.configure(text='диалог с ai', text_color='gold3')
        frame_right = ctk.CTkFrame(frame)
        self._text_area = ctk.CTkTextbox(frame_right, width=550)
        # добавить переключение в зависимости от темы, так как на светлой плохо видно белый текст
        self._text_area.tag_config('ai', foreground="#10B981")
        self._text_area.tag_config('user', foreground="white")
        # self._text_area.tag_config('tag', foreground="yellow")
        self._text_area.pack(expand=True, fill='both', padx=10, pady=10)
        frame_right.pack(expand=True, fill='both', side='right', padx=10, pady=10)
