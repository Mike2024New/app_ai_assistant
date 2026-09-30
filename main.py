import threading
from infrastructure_tk_ui import widgets, StyleManager, get_standart_styles, themes_standart
from tkinter import ttk
import asyncio
from infrastructure_path_utils import get_root_dir_path
from config import settings
from moduls import Launcher
from pipeline import Pipeline
from edit_settings import SettingsEdit

"""
Минимальный ui - mvp, для теста всей сборки компонентов
"""


class AIAssistant:
    def __init__(self):
        self._is_running = False
        self._destroy = False
        self._run_thread: threading.Thread | None = None
        self._padx, self._pady = 5, 5
        self._root = widgets.RootWidget(size=(500, 500), resizable=(True, True))
        self._root.form.title('ai ассистент')
        thema = themes_standart.LightBeige(FONT=('calibry', 12))
        thema = get_standart_styles(thema)
        self._style_manager = StyleManager(themes=[thema])
        self._display: ttk.Label | None = None
        self._queue_dialog: asyncio.Queue | None = None
        self._text_area_chat: widgets.TextWidget | None = None
        self.main_window()
        self._root.form.protocol('WM_DELETE_WINDOW', self._on_close)
        self._root.form.mainloop()

    async def dialog_observer(self):
        """Получает сообщения из очереди и показывает, что говорил пользователь а что ИИ"""
        while self._is_running:
            await asyncio.sleep(0.01)
            res = await self._queue_dialog.get()
            self._root.form.after(0, lambda: self._text_area_chat.insert_text(f"{res}\n{'-' * 50}\n"))

    async def run(self):
        self._is_running = True
        self._queue_dialog = asyncio.Queue()  # новая очередь для общения с моделью
        launcher = Launcher(target_dir=get_root_dir_path())
        self._root.form.after(0, lambda: self._display.configure(text='запуск ассистента подождите...',
                                                                 foreground='tomato'))
        await launcher.start(services=settings.services, log_level='info')
        asyncio.create_task(self.dialog_observer())
        pipeline = Pipeline(services=launcher.run_services, queue_dialog=self._queue_dialog)
        await pipeline.start()  # запуск конвейрера (комбинации сервисов)

        self._root.form.after(0, lambda: self._display.configure(text='ассистент запущен', foreground='green'))

        while self._is_running:
            await asyncio.sleep(0.05)

        await pipeline.stop()  # остановить конвейер (комбинации сервисов)
        await launcher.stop()  # остановить сервера
        self._root.form.after(0, lambda: self._display.configure(text='', foreground='green'))
        if self._destroy:
            self._root.form.destroy()

    def main_window(self):
        self._root.form.configure(padx=self._padx, pady=self._pady)
        frame = ttk.Frame(self._root.form)
        btn1 = ttk.Button(frame, text='запуск')
        btn2 = ttk.Button(frame, text='стоп')
        btn3 = ttk.Button(frame, text='опции')

        def run_callback():
            if not self._is_running:
                self._run_thread = threading.Thread(target=lambda: asyncio.run(self.run()), daemon=True)
                self._run_thread.start()

        def stop_callback():
            if self._is_running:
                self._root.form.after(0, lambda: self._display.configure(
                    text='подождите идет остановка ассистента...',
                    foreground='tomato',
                ))
                self._is_running = False

        btn1.pack(side='left', expand=True, fill='x', anchor='nw', padx=self._padx, pady=self._pady)
        btn2.pack(side='left', expand=True, fill='x', anchor='nw', padx=self._padx, pady=self._pady)
        btn3.pack(side='left', expand=True, fill='x', anchor='nw', padx=self._padx, pady=self._pady)
        btn1.configure(command=lambda: run_callback())
        btn2.configure(command=lambda: stop_callback())
        btn3.configure(command=lambda: self.settings_window())

        frame.pack(fill='x')
        frame2 = ttk.Frame(self._root.form)

        self._display = ttk.Label(frame2, text='')
        self._display.pack(anchor='nw', padx=self._padx, pady=self._pady)

        self._text_area_chat = widgets.TextWidget(parent=frame2, editable=False)
        self._text_area_chat.form.pack(expand=True, fill='both')
        frame2.pack(expand=True, fill='both', padx=self._padx, pady=self._pady)
        self._style_manager.apply(container=self._root.form)

    def settings_window(self):
        modal_window = widgets.RootWidget(parent=self._root.form, modal=True, resizable=(True, True))
        modal_window.form.configure(padx=self._padx, pady=self._pady)

        frame = ttk.Frame(modal_window.form)
        frame.pack(expand=True, fill='both')

        # ----------------- системный промпт ----------------------------
        frame2 = ttk.Frame(frame)
        frame2.pack(expand=True, fill='both')
        label = ttk.Label(frame2, text='системный промпт:')
        text_area_system_prompt = widgets.TextWidget(frame2, editable=True)
        text_area_system_prompt.form.configure(height=15)
        text_area_system_prompt.insert_text(SettingsEdit.llm_get_system_prompt())
        label.pack(anchor='nw', padx=self._padx, pady=self._pady)
        text_area_system_prompt.form.pack(expand=True, fill='both', padx=self._padx, pady=self._pady)

        # ---------------- выбор модели ----------------------------
        frame3 = ttk.Frame(frame)
        frame3.pack(expand=True, fill='both')
        ttk.Label(frame3, text='Выберите модель:').pack(side='left', anchor='w', padx=self._padx, pady=self._pady)
        model_combo = widgets.ComboBoxTTK(
            parent=frame3,
            default=SettingsEdit.llm_get_current_model(),
            values=SettingsEdit.llm_get_models_list(),
        )
        model_combo.form.pack(expand=True, fill='x', side='left', padx=self._padx, pady=self._pady)

        # ---------------- числовые опции ----------------------------
        frame3 = ttk.Frame(frame)
        frame3.pack(expand=True, fill='both')

        ttk.Label(frame3, text='размер контекста:').pack(side='left', padx=self._padx, pady=self._pady)
        n_ctx_spinbox = ttk.Spinbox(frame3, from_=0, to=512000, increment=1, width=8)
        n_ctx_spinbox.set(SettingsEdit.llm_get_n_ctx())
        n_ctx_spinbox.pack(side='left', padx=self._padx, pady=self._pady)

        ttk.Label(frame3, text='температура:').pack(side='left', padx=self._padx, pady=self._pady)
        temperature_spinbox = ttk.Spinbox(frame3, from_=0.0, to=2.0, increment=0.1, width=8)
        temperature_spinbox.set(SettingsEdit.llm_get_temperature())
        temperature_spinbox.pack(side='left', padx=self._padx, pady=self._pady)

        ttk.Label(frame3, text='длина ответа в токенах:').pack(side='left', padx=self._padx, pady=self._pady)
        max_tokens_spinbox = ttk.Spinbox(frame3, from_=0, to=64000, increment=1, width=8)
        max_tokens_spinbox.set(SettingsEdit.llm_get_max_tokens())
        max_tokens_spinbox.pack(side='left', padx=self._padx, pady=self._pady)

        frame4 = ttk.Frame(frame)
        frame4.pack(expand=True, fill='both')
        one_message_mode_check_box = widgets.CheckboxWidgetTTK(parent=frame4, text='режим вопрос ответ')
        one_message_mode_check_box.set(value=SettingsEdit.llm_get_one_message_mode())
        one_message_mode_check_box.form.pack(fill='x', side='left', padx=self._padx, pady=self._pady)

        # ----------------- кнопка обновить настройки ---------------

        def update_settings():
            system_prompt = text_area_system_prompt.get_text()
            SettingsEdit.llm_edit_system_prompt(prompt=system_prompt)
            SettingsEdit.llm_edit_model(model=model_combo.get_value())
            SettingsEdit.llm_edit_one_message_mode(one_message_mode_check_box.get())
            SettingsEdit.llm_edit_temperature(float(temperature_spinbox.get()))
            SettingsEdit.llm_edit_n_ctx(int(n_ctx_spinbox.get()))
            SettingsEdit.llm_edit_max_tokens(int(max_tokens_spinbox.get()))
            modal_window.form.destroy()

        btn_update_settings = ttk.Button(frame, text='Обновить настройки')
        btn_update_settings.configure(command=lambda: update_settings())
        btn_update_settings.pack(fill='x', padx=self._padx, pady=self._pady)
        self._style_manager.apply(container=modal_window.form)

    def _on_close(self):
        """Выход из диалога если нажали крест"""
        if self._is_running:
            self._root.form.after(0, lambda: self._display.configure(
                text='подождите идет остановка ассистента...',
                foreground='tomato',
            ))
            self._is_running = False  # закрытие окна приложения
            self._destroy = True
        else:
            self._root.form.destroy()


if __name__ == '__main__':
    ai = AIAssistant()
