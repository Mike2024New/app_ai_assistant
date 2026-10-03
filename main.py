import threading

from infrastructure_http_clients import DownloadFileType, file_downloader
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
        self._pipeline: Pipeline | None = None
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

        try:
            self._pipeline = Pipeline(services=launcher.run_services, queue_dialog=self._queue_dialog)
            await self._pipeline.start()  # запуск конвейрера (комбинации сервисов)
        except Exception as err:
            msg = f'Авария, не удалось запустить ассистента {err}'
            self._root.form.after(0, lambda: self._display.configure(text=msg, foreground='red'))
            await launcher.stop()
            self._is_running = False
            return

        self._root.form.after(0, lambda: self._display.configure(text='ассистент запущен', foreground='green'))

        while self._is_running:
            await asyncio.sleep(0.05)

        await self._pipeline.stop()  # остановить конвейер (комбинации сервисов)
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
        ttk.Label(frame3, text='Модель llm:').pack(side='left', anchor='w', padx=self._padx, pady=self._pady)
        llm_model_combo = widgets.ComboBoxTTK(
            parent=frame3,
            default=SettingsEdit.llm_get_current_model(),
            values=SettingsEdit.llm_get_models_list(),
        )
        llm_model_combo.form.pack(expand=True, fill='both', side='left', padx=self._padx, pady=self._pady)

        # ---------------- выбор модели ----------------------------
        frame2_1 = ttk.Frame(frame)
        frame2_1.pack(expand=True, fill='both')
        ttk.Label(frame2_1, text='Модель stt:').pack(side='left', anchor='w', padx=self._padx, pady=self._pady)
        stt_model_combo = widgets.ComboBoxTTK(
            parent=frame2_1,
            default=SettingsEdit.stt_get_current_model(),
            values=SettingsEdit.stt_get_models_list(),
        )
        stt_model_combo.form.pack(expand=True, fill='both', side='left', padx=self._padx, pady=self._pady)

        # ---------------- выбор модели tts ----------------------------

        frame2_2 = ttk.Frame(frame)
        frame2_2.pack(expand=True, fill='both')
        ttk.Label(frame2_2, text='Модель tts ru:').pack(side='left', anchor='w', padx=self._padx, pady=self._pady)

        tts_models = SettingsEdit.tts_get_allowed_voices_list()
        tts_voice_model_ru_combo = widgets.ComboBoxTTK(
            parent=frame2_2,
            default=SettingsEdit.tts_get_current_voices()['ru'],
            values=tts_models['ru'],
        )
        tts_voice_model_ru_combo.form.pack(expand=True, fill='both', side='left', padx=self._padx, pady=self._pady)
        ttk.Label(frame2_2, text='Модель tts en:').pack(side='left', anchor='w', padx=self._padx, pady=self._pady)
        tts_voice_model_en_combo = widgets.ComboBoxTTK(
            parent=frame2_2,
            default=SettingsEdit.tts_get_current_voices()['en'],
            values=tts_models['en'],
        )

        tts_voice_model_en_combo.form.pack(expand=True, fill='both', side='left', padx=self._padx, pady=self._pady)

        # ---------------- числовые опции -------------------------------
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
            SettingsEdit.llm_edit_model(model=llm_model_combo.get_value())
            SettingsEdit.stt_edit_model(model=stt_model_combo.get_value())
            SettingsEdit.llm_edit_one_message_mode(one_message_mode_check_box.get())
            # редактирование голосов моделей
            SettingsEdit.tts_edit_voices(voice=tts_voice_model_ru_combo.get_value(), lang='ru')
            SettingsEdit.tts_edit_voices(voice=tts_voice_model_en_combo.get_value(), lang='en')
            SettingsEdit.llm_edit_temperature(float(temperature_spinbox.get()))
            SettingsEdit.llm_edit_n_ctx(int(n_ctx_spinbox.get()))
            SettingsEdit.llm_edit_max_tokens(int(max_tokens_spinbox.get()))
            self._tts_running = False
            modal_window.form.destroy()

        btn_update_settings = ttk.Button(frame, text='Обновить настройки')
        btn_update_settings.configure(command=lambda: update_settings())
        btn_update_settings.pack(fill='x', padx=self._padx, pady=self._pady, side='left')
        btn_addons = ttk.Button(frame, text='дополнительно', command=lambda: self.added_materials_window())
        btn_addons.pack(fill='x', padx=self._padx, pady=self._pady, side='left')
        self._style_manager.apply(container=modal_window.form)

    def added_materials_window(self):
        root = widgets.RootWidget(modal=True, parent=self._root.form)
        text_area = widgets.TextWidget(parent=root.form)
        text_area.form.configure(height=10)
        text_area.form.pack(expand=True, fill='both')
        text_area.insert_text(text='Скачать дополнительные материалы, для сильных машин, видеокарта cuda от 8gb VRAM')

        def run_callback(text_box):
            threading.Thread(
                target=lambda: asyncio.run(self.download_assets(root=root.form, text_box=text_box)),
                daemon=True,
            ).start()

        btn = ttk.Button(root.form, text='скачать', command=lambda: run_callback(text_box=text_area))
        btn.pack(expand=True, fill='both')
        self._style_manager.apply(container=root.form)

    @staticmethod
    async def download_assets(root, text_box):
        downloads_list = []
        # сбор ulr
        root_dir = get_root_dir_path()
        for svc_name in settings.assets:
            for dirname in settings.assets[svc_name]:
                for key, val in dirname.items():
                    td = root_dir / svc_name / 'resources' / 'models'
                    if "*" not in key:  # если есть * в названии то извлечь в корень models
                        td = td / key
                    downloads_list.append(
                        DownloadFileType(
                            url_list=val,
                            filename=key,
                            target_dir=td,
                        )
                    )

        async def observer(queue_in: asyncio.Queue):
            while True:
                res = await queue_in.get()
                if res is None:
                    break
                # обновление строки, для одиночных загрузок. Для мультизагрузки лучше таблицы rich
                text_box.clear_text()
                row = '\n'.join([f'{k} {v}%' for k, v in res.items()])
                text_box.insert_text(text=row)

        queue = asyncio.Queue()
        asyncio.create_task(observer(queue_in=queue))
        await file_downloader(download_list=downloads_list, feedback_queue=queue, timeout=60)
        root.destroy()

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
