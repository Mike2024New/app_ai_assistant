from config import settings, settings_manager
from infrastructure_path_utils import get_root_dir_path

root_dir = get_root_dir_path()


class SettingsEdit:
    @staticmethod
    def llm_get_system_prompt():
        return settings.services['srv_llm']['system_prompt']

    @staticmethod
    def llm_edit_system_prompt(prompt: str):
        settings.services['srv_llm']['system_prompt'] = prompt
        settings_manager.apply_new_settings(settings=settings)

    @staticmethod
    def llm_get_one_message_mode():
        return settings.services['srv_llm']['one_message_mode']

    @staticmethod
    def llm_edit_one_message_mode(value: bool):
        settings.services['srv_llm']['one_message_mode'] = value
        settings_manager.apply_new_settings(settings=settings)

    @staticmethod
    def llm_get_n_ctx():
        return settings.services['srv_llm']['n_ctx']

    @staticmethod
    def llm_edit_n_ctx(value: int):
        settings.services['srv_llm']['n_ctx'] = value
        settings_manager.apply_new_settings(settings=settings)

    @staticmethod
    def llm_get_temperature():
        return settings.services['srv_llm']['temperature']

    @staticmethod
    def llm_edit_temperature(value: float):
        settings.services['srv_llm']['temperature'] = value
        settings_manager.apply_new_settings(settings=settings)

    @staticmethod
    def llm_get_max_tokens():
        return settings.services['srv_llm']['max_tokens']

    @staticmethod
    def llm_edit_max_tokens(value: int):
        settings.services['srv_llm']['max_tokens'] = value
        settings_manager.apply_new_settings(settings=settings)

    @staticmethod
    def llm_get_current_model():
        return settings.services['srv_llm']['model']

    @staticmethod
    def llm_get_models_list():
        models_dir = root_dir / 'srv_llm' / 'resources' / 'models'
        models = [file.name for file in models_dir.iterdir() if file.suffix == '.gguf']
        return models

    @classmethod
    def llm_edit_model(cls, model: str):
        models = cls.llm_get_models_list()
        if model in models:
            settings.services['srv_llm']['model'] = model
            settings_manager.apply_new_settings(settings=settings)


if __name__ == '__main__':
    SettingsEdit.llm_edit_one_message_mode(value=False)
    SettingsEdit.llm_edit_system_prompt(prompt='Ты мой виртуальный друг. Давай общаться без маркдаунов.')
    # SettingsEdit.llm_edit_model(model='gemma-3-4b-it-Q4_K_M.gguf')
    # SettingsEdit.llm_edit_system_n_ctx(value=32000)
