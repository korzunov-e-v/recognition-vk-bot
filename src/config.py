import logging

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ServiceSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    flow: str = Field(
        "direct", description="Режим работы ('direct'/'button'), используется класс VkDirectFlow или VkButtonFlow."
    )

    app_name: str = "recognition-vk-bot"
    log_level: int = Field(logging.INFO, description="Уровень логирования")
    group_access_token: str = Field(description="Токен доступа группы Вконтакте")
    group_id: int = Field(description="ID группы Вконтакте")

    vk_api_token: str = Field(description="Сервисный ключ приложения Вконтакте")
    vision_api_token: str = Field(description="Сервисный токен для Vision")


service_settings = ServiceSettings()
