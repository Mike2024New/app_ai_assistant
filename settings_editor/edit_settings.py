import json
from typing import Literal
from config import settings, settings_manager
from infrastructure_path_utils import get_root_dir_path
from settings_editor.default_settings import default_settings
from config.schemas import Settings


class SettingsEditor:

    @staticmethod
    def reset_settings() -> Settings:
        new_settings = Settings.model_validate(default_settings)
        settings_manager.apply_new_settings(settings=new_settings)
        return new_settings

    # ========================== ALL ==========================
    @staticmethod
    def companion_get():
        return settings.companion

    @staticmethod
    def companion_set(val: bool):
        settings.companion = val
        settings_manager.apply_new_settings(settings=settings)

    @staticmethod
    def assistant_get():
        return settings.assistant

    @staticmethod
    def assistant_set(val: bool):
        settings.assistant = val
        settings_manager.apply_new_settings(settings=settings)

    # ========================== TTS ==========================
    @staticmethod
    def tts_get_speakers_list(lang: Literal['ru', 'en']) -> list[str]:
        """Получение списка голосов для текущей модели (которая прописана в настройках settings.json)"""
        models_info_path = get_root_dir_path().parent / 'srv_tts' / 'resources' / 'models' / 'models_info.json'
        if not models_info_path.exists():
            raise RuntimeError(f'Файл с конфигурацией спикеров не найден в srv_tts')
        try:
            with open(file=models_info_path, mode='r', encoding='utf-8') as f:
                data = json.loads(f.read())
                for key in settings.services['srv_tts']['models']:
                    if lang in key:
                        return data[key]
            return []
        except Exception:  # noqa
            return []

    @staticmethod
    def tts_get_current_speaker(lang: Literal['ru', 'en']):
        """Получить текущего спикера (en/ru)"""
        return settings.speakers[lang]

    @classmethod
    def tts_set_current_speaker(cls, lang: Literal['ru', 'en'], speaker: str):
        """Установить спикера (en/ru)"""
        speakers = cls.tts_get_speakers_list(lang=lang)
        if speaker not in speakers:
            raise ValueError(f'Голос `{speaker}` отсутствует в списке {speakers}')
        settings.speakers[lang] = speaker
        settings_manager.apply_new_settings(settings=settings)

    # ========================== STT ==========================
    @staticmethod
    def stt_get_numbers_filter():
        """Установка фильтра чисел -> выдает числа текстом"""
        return settings.stt_numbers_filter

    @staticmethod
    def stt_set_numbers_filter(val: bool):
        """Установка фильтра чисел -> выдает числа текстом"""
        settings.stt_numbers_filter = val
        settings_manager.apply_new_settings(settings=settings)

    @staticmethod
    def stt_get_models_list():
        models_info_path = get_root_dir_path().parent / 'srv_stt' / 'resources' / 'models'
        if not models_info_path.exists():
            raise RuntimeError(f'Директория с stt моделями не найдена')
        models = [file.name for file in models_info_path.iterdir() if file.is_dir()]
        return models

    @staticmethod
    def stt_get_current_model():
        return settings.services['srv_stt']['model']

    @classmethod
    def stt_set_current_model(cls, model: str):
        models = cls.stt_get_models_list()
        if model not in models:
            raise RuntimeError(f'Не найдена модель распознавания речи {model}, доступны {models}')
        settings.services['srv_stt']['model'] = model
        settings_manager.apply_new_settings(settings=settings)

    # ========================== LLM ==========================
    @staticmethod
    def llm_get_models_list():
        models_info_path = get_root_dir_path().parent / 'srv_llm' / 'resources' / 'models'
        if not models_info_path.exists():
            raise RuntimeError(f'Директория с llm моделями не найдена')
        models = [file.name for file in models_info_path.iterdir() if file.suffix == '.gguf']
        return models

    @staticmethod
    def llm_get_current_model():
        return settings.services['srv_llm']['model']

    @classmethod
    def llm_set_current_model(cls, model: str):
        models = cls.llm_get_models_list()
        if model not in models:
            raise RuntimeError(f'Не найдена llm модель {model}, доступны {models}')
        settings.services['srv_llm']['model'] = model
        settings_manager.apply_new_settings(settings=settings)

    @staticmethod
    def llm_get_n_ctx():
        return settings.services['srv_llm']['n_ctx']

    @staticmethod
    def llm_set_n_ctx(val: int = 32768):
        if not 0 < val < 512000:
            raise ValueError(f'Длина контекста может быть в пределах от 0 до 512000')
        settings.services['srv_llm']['n_ctx'] = val
        settings_manager.apply_new_settings(settings=settings)

    @staticmethod
    def llm_get_temperature():
        return settings.services['srv_llm']['temperature']

    @staticmethod
    def llm_set_temperature(val: float = 0.5):
        if not 0 < val <= 10:
            raise ValueError(f'Температура модели может быть в пределах от 0 до 10')
        settings.services['srv_llm']['temperature'] = val
        settings_manager.apply_new_settings(settings=settings)

    @staticmethod
    def llm_get_max_tokens():
        return settings.services['srv_llm']['max_tokens']

    @staticmethod
    def llm_set_max_tokens(val: int = 256):
        if not 0 < val <= 65536:
            raise ValueError(f'Максимальное кол-во токенов от 0 до 65536')
        settings.services['srv_llm']['max_tokens'] = val
        settings_manager.apply_new_settings(settings=settings)

    @staticmethod
    def llm_get_system_prompt():
        return settings.services['srv_llm']['system_prompt']

    @staticmethod
    def llm_set_system_prompt(val: str):
        settings.services['srv_llm']['system_prompt'] = val
        settings_manager.apply_new_settings(settings=settings)

    @staticmethod
    def llm_get_processor_power_percentage():
        return settings.services['srv_llm']['processor_power_percentage']

    @staticmethod
    def llm_set_processor_power_percentage(val: int = 80):
        if not 10 < val <= 100:
            raise ValueError(f'Используемая мощность процессора должна находиться в пределах от 10 до 100')
        settings.services['srv_llm']['processor_power_percentage'] = val
        settings_manager.apply_new_settings(settings=settings)

    @staticmethod
    def llm_get_one_message_mode() -> bool:
        return settings.services['srv_llm']['one_message_mode']

    @staticmethod
    def llm_set_one_message_mode(val: bool = False):
        settings.services['srv_llm']['one_message_mode'] = val
        settings_manager.apply_new_settings(settings=settings)

    @staticmethod
    def llm_get_use_mmap() -> bool:
        return settings.services['srv_llm']['use_mmap']

    @staticmethod
    def llm_set_use_mmap(val: bool = False):
        settings.services['srv_llm']['use_mmap'] = val
        settings_manager.apply_new_settings(settings=settings)


if __name__ == '__main__':
    print(SettingsEditor.llm_get_models_list())
