import os
import subprocess
import threading

from config import history_messages_json
import customtkinter as ctk
from config import logger
from config import SettingsEditor
from infrastructure_path_utils import get_root_dir_path
from CTkToolTip import CTkToolTip


class SettingsWindow:
    def __init__(self):
        self._settings = SettingsEditor()

        self._root: ctk.CTk | None = None
        self._frame: ctk.CTkFrame | None = None
        self._row_state: ctk.CTkLabel | None = None
        self._storage: dict | None = None

        self._llm_model_combobox: ctk.CTkComboBox | None = None
        self._llm_prompt_text_area: ctk.CTkTextbox | None = None
        self._llm_one_message_checkbox: ctk.CTkCheckBox | None = None
        self._llm_max_tokens: ctk.CTkEntry | None = None
        self._llm_n_ctx: ctk.CTkEntry | None = None
        self._llm_temperature: ctk.CTkEntry | None = None
        self._llm_processor_power_percentage: ctk.CTkEntry | None = None
        self._llm_use_mmap_checkbox: ctk.CTkCheckBox | None = None
        self._stt_model_combobox: ctk.CTkComboBox | None = None
        self._tts_ru_combobox: ctk.CTkComboBox | None = None
        self._tts_en_combobox: ctk.CTkComboBox | None = None

        self._stt_numbers_filter_swith: ctk.CTkSwitch | None = None

        self._companion_swith: ctk.CTkSwitch | None = None
        self._assistant_swith: ctk.CTkSwitch | None = None

        self._assist_name_cmd_swith: ctk.CTkSwitch | None = None
        self._assistant_name: ctk.CTkEntry | None = None

        self._assist_speech_swith: ctk.CTkSwitch | None = None

        self._padx, self._pady = 10, 10

    def apply_settings(self):
        """Применение выбранных параметров"""
        try:
            self._settings.llm_set_current_model(model=self._llm_model_combobox.get())
            self._settings.llm_set_one_message_mode(val=bool(self._llm_one_message_checkbox.get()))
            self._settings.llm_set_system_prompt(val=self._llm_prompt_text_area.get('1.0', 'end-1c'))
            self._settings.llm_set_use_mmap(val=bool(self._llm_use_mmap_checkbox.get()))
            # установка настроек второй группы полей
            self._settings.llm_set_n_ctx(val=int(self._llm_n_ctx.get()))
            self._settings.llm_set_max_tokens(val=int(self._llm_max_tokens.get()))
            self._settings.llm_set_temperature(val=float(self._llm_temperature.get().replace(',', '.')))
            self._settings.llm_set_processor_power_percentage(val=int(self._llm_processor_power_percentage.get()))
            # третья группа полей
            self._settings.stt_set_current_model(model=self._stt_model_combobox.get())
            self._settings.stt_set_numbers_filter(val=bool(self._stt_numbers_filter_swith.get()))


            self._settings.tts_set_current_speaker(speaker=self._tts_ru_combobox.get(), lang='ru')
            self._settings.tts_set_current_speaker(speaker=self._tts_en_combobox.get(), lang='en')


            self._settings.companion_set(val=bool(self._companion_swith.get()))
            self._settings.assistant_set(val=bool(self._assistant_swith.get()))
            self._settings.assistant_name_in_cmd_set(val=bool(self._assist_name_cmd_swith.get()))
            self._settings.assistant_name_set(self._assistant_name.get().strip())
            self._settings.assistant_speech_set(val=bool(self._assist_speech_swith.get()))

            msg = 'Настройки сохранены и вступят в силу после перезагрузки ассистента'
            self._row_state.configure(text_color='green4', text=msg)
        # обработка, любого возникшего исключения
        except Exception as err:
            msg = f'Ошибка применения настроек: {err}'
            self._row_state.configure(text_color='red2', text=msg)

    def window(self, root: ctk.CTk, frame: ctk.CTkFrame, row_state: ctk.CTkLabel, storage: dict):
        self._root = root
        self._frame = frame
        self._row_state = row_state
        self._storage = storage
        body_header_label = ctk.CTkLabel(frame, text='Настройки')
        body_header_label.configure(font=('roboto', 18, 'bold'))
        body_header_label.pack(side='top', anchor='nw', padx=10, pady=(self._padx / 2, self._pady / 2))

        # макет окна с помощью фреймов
        frame_main = ctk.CTkFrame(frame, fg_color='transparent', border_width=0)
        frame_left = ctk.CTkFrame(frame_main, fg_color='transparent', border_width=2)
        frame_center = ctk.CTkFrame(frame_main, fg_color='transparent', border_width=2)
        frame_right = ctk.CTkFrame(frame_main, fg_color='transparent', border_width=2)
        frame_left.pack(expand=True, fill='both', side='left', padx=self._padx / 2, pady=0)
        frame_center.pack(expand=False, fill='both', side='left', padx=self._padx / 2, pady=0)
        frame_right.pack(expand=False, fill='both', side='left', padx=self._padx / 2, pady=0)
        frame_main.pack(expand=True, fill='both', padx=0, pady=0)
        # =========================== LEFT_FRAME =============================================
        self._llm_model_combobox = ctk.CTkComboBox(frame_left)
        self._llm_model_combobox.pack(expand=False, fill='both', padx=self._padx, pady=self._pady)

        self._llm_prompt_text_area = ctk.CTkTextbox(frame_left, width=300)
        self._llm_prompt_text_area.pack(expand=True, fill='both', padx=self._padx, pady=self._pady)

        # =========================== CENTRAL_FRAME =============================================
        # n_ctx
        frame1 = ctk.CTkFrame(frame_center, fg_color='transparent', border_width=0)
        frame1.pack(expand=False, fill='x', padx=self._padx, pady=self._pady)
        ctk.CTkLabel(
            frame1, text='n_ctx: ', fg_color='transparent'
        ).pack(expand=False, side='left', fill='x')
        self._llm_n_ctx = ctk.CTkEntry(frame1, width=150)
        self._llm_n_ctx.pack(expand=False, fill='x', side='right', anchor='e')

        # max_tokens
        frame2 = ctk.CTkFrame(frame_center, fg_color='transparent', border_width=0)
        frame2.pack(expand=False, fill='x', padx=self._padx, pady=self._pady)
        ctk.CTkLabel(
            frame2, text='max_tokens: ', fg_color='transparent'
        ).pack(expand=False, side='left', fill='x')
        self._llm_max_tokens = ctk.CTkEntry(frame2, width=150)
        self._llm_max_tokens.pack(expand=False, fill='x', side='right')
        # temperature
        frame3 = ctk.CTkFrame(frame_center, fg_color='transparent', border_width=0)
        frame3.pack(expand=False, fill='x', padx=self._padx, pady=self._pady)
        ctk.CTkLabel(
            frame3, text='temperature: ', fg_color='transparent'
        ).pack(expand=False, side='left', fill='x')
        self._llm_temperature = ctk.CTkEntry(frame3, width=150)
        self._llm_temperature.pack(expand=False, fill='x', side='right')
        # cpu percentage
        frame4 = ctk.CTkFrame(frame_center, fg_color='transparent', border_width=0)
        frame4.pack(expand=False, fill='x', padx=self._padx, pady=self._pady)
        ctk.CTkLabel(
            frame4, text='processor power: ', fg_color='transparent'
        ).pack(expand=False, side='left', fill='x')
        self._llm_processor_power_percentage = ctk.CTkEntry(frame4, width=150)
        self._llm_processor_power_percentage.pack(expand=False, fill='x', side='right')

        self._llm_one_message_checkbox = ctk.CTkCheckBox(frame_center, text='Режим вопрос ответ')
        self._llm_one_message_checkbox.pack(expand=False, fill='both', padx=self._padx, pady=self._pady)

        self._llm_use_mmap_checkbox = ctk.CTkCheckBox(frame_center, text='Экономия RAM (use_mmap)')
        self._llm_use_mmap_checkbox.pack(expand=False, fill='both', padx=self._padx, pady=self._pady)

        def clear_history():
            if history_messages_json.exists():
                os.remove(history_messages_json)
                llm_clear_history_btn.configure(state='disabled')

        llm_clear_history_btn = ctk.CTkButton(frame_center, text='Сбросить summary', command=lambda: clear_history())
        llm_clear_history_btn.configure(state='normal' if history_messages_json.exists() else 'disabled')
        llm_clear_history_btn.pack(expand=False, fill='both', padx=self._padx, pady=self._pady)
        log_colapse_btn = ctk.CTkButton(
            frame_center, text='Собрать логи', command=lambda: log_colapse_callback()
        )

        def log_colapse_callback():
            """сбор логов компонентов приложения, для отладки"""
            from utils import log_colapse
            from metric import monitor
            import pythoncom
            self._row_state.configure(text='Идет сборка логов, подождите...', text_color='gold3')

            def log_func():
                try:
                    log_colapse_btn.configure(state='disabled')
                    pythoncom.CoInitialize()
                    r = monitor()
                    logger.info(f'[ LOG_COLAPSE_INFO ] Информация о системе: {r}')
                except Exception as err:
                    logger.error(f'[ LOG_COLAPSE_INFO ] Не удалось собрать информацию о системе {err}')
                finally:
                    pythoncom.CoUninitialize()
                    log_colapse_btn.configure(state='normal')

                log_path = log_colapse()
                subprocess.Popen(['explorer', str(log_path.parent)])
                self._row_state.after(
                    0, lambda:
                    self._row_state.configure(text='Сборка логов, завершена.', text_color='green')
                )  # noqa

            threading.Thread(target=log_func, daemon=True).start()

        log_colapse_btn.pack(expand=False, fill='both', padx=self._padx, pady=self._pady)

        root_dir_btn = ctk.CTkButton(
            frame_center, text='Папка приложения',
            command=lambda: subprocess.Popen(['explorer', str(get_root_dir_path())])
        )
        root_dir_btn.pack(expand=False, fill='both', padx=self._padx, pady=self._pady)

        # =========================== RIGHT_FRAME =============================================
        # выбор tts модели и голоса
        # настройки для ru озвучки
        frame6 = ctk.CTkFrame(frame_right, fg_color='transparent', border_width=0)
        frame6.pack(expand=False, fill='x', padx=self._padx, pady=self._pady)
        label = ctk.CTkLabel(frame6, text='голос ru: ')
        label.pack(expand=False, side='left', fill='x')
        self._tts_ru_combobox = ctk.CTkComboBox(frame6, width=200)
        self._tts_ru_combobox.pack(expand=False, fill='x', side='right')
        CTkToolTip(
            self._tts_ru_combobox,
            message='Голос, которым ассистент будет разговаривать на русском языке',
            delay=0.5, wraplength=250,
        )

        # настройки для en озвучки
        frame7 = ctk.CTkFrame(frame_right, fg_color='transparent', border_width=0)
        frame7.pack(expand=False, fill='x', padx=self._padx, pady=self._pady)
        label = ctk.CTkLabel(frame7, text='голос en: ')
        label.pack(expand=False, side='left', fill='x')
        self._tts_en_combobox = ctk.CTkComboBox(frame7, width=200)
        self._tts_en_combobox.pack(expand=False, fill='x', side='right')
        CTkToolTip(
            self._tts_en_combobox,
            message='Голос, которым ассистент будет разговаривать на английском языке',
            delay=0.5, wraplength=250,
        )

        # выбор stt модели
        frame5 = ctk.CTkFrame(frame_right, fg_color='transparent', border_width=0)
        frame5.pack(expand=False, fill='x', padx=self._padx, pady=self._pady)
        label = ctk.CTkLabel(frame5, text='stt модель: ')
        label.pack(expand=False, side='left', fill='x')
        self._stt_model_combobox = ctk.CTkComboBox(frame5, width=200)
        self._stt_model_combobox.pack(expand=False, fill='x', side='right')
        CTkToolTip(
            self._stt_model_combobox,
            message="Модель распознавания речи (Whisper). Vosk используется всегда по умолчанию для быстрого старта.\n- small: Быстрая, подходит для слабых ПК или без видеокарты, но менее точная.\n- medium: Хорошая точность, рекомендуется при наличии видеокарты (лучше с CUDA).\n- large: Максимальная точность, но требует много ресурсов.\n\nСовет: Если у вас видеокарта NVIDIA, установите драйвер CUDA для ускорения работы.",
            delay=0.5, wraplength=250,
        )

        frame5_5 = ctk.CTkFrame(frame_right, fg_color='transparent', border_width=0)
        frame5_5.pack(expand=False, fill='x', padx=self._padx, pady=self._pady)
        self._stt_numbers_filter_swith = ctk.CTkSwitch(frame5_5, text='Числа текстом (whisper)')
        self._stt_numbers_filter_swith.set(True)
        self._stt_numbers_filter_swith.pack(expand=False, fill='x', side='left')
        CTkToolTip(
            self._stt_numbers_filter_swith,
            message="Если включено, все числа будут проговариваться словами (например, 'три', а не '3'). Особенно полезно при использовании модели Whisper, так как она может путать цифры.",
            delay=0.5, wraplength=250,
        )

        frame8 = ctk.CTkFrame(frame_right, fg_color='transparent', border_width=0)
        frame8.pack(expand=False, fill='x', padx=self._padx, pady=self._pady)
        self._companion_swith = ctk.CTkSwitch(frame8, text='Компаньон вкл')
        self._companion_swith.set(True)
        self._companion_swith.pack(expand=False, fill='x', side='left')
        CTkToolTip(
            self._companion_swith,
            message='Включает режим простого общения с ИИ (диалоги как с человеком). '
                    'Ассистент будет помнить контекст беседы (сохранять краткое резюме) для следующего раза.',
            delay=0.5, wraplength=250,
        )

        # имя ассистента
        frame8_5 = ctk.CTkFrame(frame_right, fg_color='transparent', border_width=0)
        frame8_5.pack(expand=False, fill='x', padx=self._padx, pady=self._pady)
        ctk.CTkLabel(
            frame8_5, text='имя ассистента: ', fg_color='transparent'
        ).pack(expand=False, side='left', fill='x')
        self._assistant_name = ctk.CTkEntry(frame8_5, width=150)
        self._assistant_name.pack(expand=False, fill='x', side='right')
        CTkToolTip(
            self._assistant_name,
            message="Имя, на которое реагирует ассистент. "
                    "Если ввести 'Шарик', то команду нужно будет начинать говорить с него, например: "
                    "'Шарик, открой рабочий стол'.",
            delay=0.5, wraplength=250,
        )

        frame9 = ctk.CTkFrame(frame_right, fg_color='transparent', border_width=0)
        frame9.pack(expand=False, fill='x', padx=self._padx, pady=self._pady)
        self._assistant_swith = ctk.CTkSwitch(frame9, text='Ассистент вкл')
        self._assistant_swith.set(True)
        self._assistant_swith.pack(expand=False, fill='x')
        CTkToolTip(
            self._assistant_swith,
            message="Разрешает ассистенту выполнять ваши скрипты (например, открывать папки или программы). "
                    "Команды настраиваются во вкладке 'Управление скриптами'.",
            delay=0.5, wraplength=250,
        )

        frame10 = ctk.CTkFrame(frame_right, fg_color='transparent', border_width=0)
        frame10.pack(expand=False, fill='x', padx=self._padx, pady=self._pady)
        self._assist_name_cmd_swith = ctk.CTkSwitch(frame10, text='Имя ассистента в cmd')
        self._assist_name_cmd_swith.set(True)
        self._assist_name_cmd_swith.pack(expand=False, fill='x')
        CTkToolTip(
            self._assist_name_cmd_swith,
            message="Если включено, команды должны начинаться с имени ассистента (например: 'Ассистент, открой папку'). "
                    "Если выключено — достаточно просто сказать 'Открой папку'. (Работает только если выключен 'Компаньон').",
            delay=0.5, wraplength=250
        )

        frame11 = ctk.CTkFrame(frame_right, fg_color='transparent', border_width=0)
        frame11.pack(expand=False, fill='x', padx=self._padx, pady=self._pady)
        self._assist_speech_swith = ctk.CTkSwitch(frame11, text='Ассистент голос')
        self._assist_speech_swith.set(True)
        self._assist_speech_swith.pack(expand=False, fill='x')
        CTkToolTip(
            self._assist_speech_swith,
            message="Если включено, ассистент будет голосом подтверждать выполнение ваших команд (например, скажет 'Открываю папку')."
                    "А также озвучивать результаты полученные из функций (если они есть).",
            delay=0.5, wraplength=250
        )

        # кнопки нижней панели (применить)
        default_btn = ctk.CTkButton(frame, text='по умолчанию', cursor='hand2', command=lambda: self.reset())
        apply_button = ctk.CTkButton(frame, text='применить', cursor='hand2', command=lambda: self.apply_settings())
        apply_button.pack(expand=False, side='right', padx=self._padx / 2, pady=self._pady)
        default_btn.pack(expand=False, side='right', padx=self._padx / 2, pady=self._pady)
        self.set_settings()
        self._row_state.configure(text_color='green4', text='редактирование настроек')

    def set_settings(self):
        # текущая llm модель
        self._llm_model_combobox.set(self._settings.llm_get_current_model())
        self._llm_model_combobox.configure(values=self._settings.llm_get_models_list())
        # системный промпт
        self._llm_prompt_text_area.delete('1.0', 'end')
        self._llm_prompt_text_area.insert('1.0', self._settings.llm_get_system_prompt())
        # без истории сообщений
        self._llm_one_message_checkbox.set(self._settings.llm_get_one_message_mode())
        # галочка use_mmap
        self._llm_use_mmap_checkbox.set(self._settings.llm_get_use_mmap())
        # размер контекста
        self._llm_n_ctx.set(self._settings.llm_get_n_ctx())
        # максимум токенов
        self._llm_max_tokens.set(self._settings.llm_get_max_tokens())
        # температура
        self._llm_temperature.set(self._settings.llm_get_temperature())
        # используемая мощьность процессора 100% -> все ядра
        self._llm_processor_power_percentage.set(self._settings.llm_get_processor_power_percentage())
        # выбор модели для stt
        self._stt_model_combobox.set(self._settings.stt_get_current_model())
        self._stt_model_combobox.configure(values=self._settings.stt_get_models_list())
        # выбор голоса для русской озвучки
        self._tts_ru_combobox.set(self._settings.tts_get_current_speaker(lang='ru'))
        self._tts_ru_combobox.configure(values=self._settings.tts_get_speakers_list(lang='ru'))
        # выбор голоса для английской озвучки
        self._tts_en_combobox.set(self._settings.tts_get_current_speaker(lang='en'))
        self._tts_en_combobox.configure(values=self._settings.tts_get_speakers_list(lang='en'))
        # фильтр числа текстом для whisper
        self._stt_numbers_filter_swith.set(self._settings.stt_get_numbers_filter())
        # галочки включения / выключения компаньона и ассистента
        self._companion_swith.set(self._settings.companion_get())
        self._assistant_swith.set(self._settings.assistant_get())
        # галочка содержания названия ассистента в команде
        self._assist_name_cmd_swith.set(self._settings.assistant_name_in_cmd_get())
        self._assistant_name.set(self._settings.assistant_name_get())
        self._assist_speech_swith.set(self._settings.assistant_speech_get())

    def reset(self):
        self._settings.reset_settings()
        self.set_settings()
