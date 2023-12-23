from vk_api import VkApi

from src.config import service_settings
from src.modules.vk.flows import VkButtonFlow, VkDirectFlow


async def start_polling() -> None:
    vk = VkApi(token=service_settings.group_access_token)

    if service_settings.flow == "direct":
        await VkDirectFlow(vk=vk).polling()
    else:
        await VkButtonFlow(vk=vk).polling()
