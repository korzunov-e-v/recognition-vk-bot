import logging
import os
import time
from asyncio.exceptions import TimeoutError

import aiohttp
from vk_api import VkApi, VkUpload

from src.config import service_settings
from src.modules import command_system
from src.modules.vk_graphic import recognize_image

logger = logging.getLogger("global_logger")
vk = VkApi(token=service_settings.group_access_token)
upload = VkUpload(vk=vk)


async def _download_image(img_url: str) -> str | None:
    logger.debug("downloading image")
    ts_start = time.perf_counter()
    async with aiohttp.ClientSession() as session:
        async with session.get(img_url) as resp:
            if resp.status != 200:
                resp_text = await resp.text()
                logger.error(
                    msg="downloading image error",
                    extra={"status code": resp.status, "response": resp_text},
                )
                return None
            data = await resp.content.read()
            filename = img_url.split("/")[-1].split("?")[0]
            temp_path = os.path.join(os.getcwd(), "tmp")
            os.makedirs(temp_path, exist_ok=True)
            file_path = os.path.join(temp_path, filename)
            with open(file_path, "wb") as f:
                f.write(data)
    duration = time.perf_counter() - ts_start
    file_size = os.stat(file_path).st_size
    logger.debug(
        msg="downloading image complete",
        extra={"duration": duration, "size_bytes": file_size},
    )
    return file_path


def prompt_handler():
    message = "Отправьте изображения для распознавания"
    attachments = []
    return message, attachments


async def command_handler(user_message: str, user_attachments: list, *args, **kwargs):
    ts_start = time.perf_counter()
    logger.debug("start image processing")

    user_photo_attachments = [
        max(att["photo"]["sizes"], key=lambda a: a["height"])["url"]
        for att in user_attachments
        if att["type"] == "photo"
    ]

    if not user_photo_attachments:
        resp_message_text, resp_attachments = "Изображений не было", []
        return resp_message_text, resp_attachments

    results = []
    for img_url in user_photo_attachments:
        try:
            img_path = await _download_image(img_url)
            result = await recognize_image(img_path)
            results.append(result["object_labels"])
        except TimeoutError as e:
            resp_message_text, resp_attachments = "Сервис VK Vision недоступен", []
            logger.error(
                msg="vk vision unavailable (TimeoutError)",
                extra={"exception": e},
            )
            return resp_message_text, resp_attachments
        except BaseException as e:
            resp_message_text, resp_attachments = "Сервис VK Vision недоступен", []
            logger.error(
                msg=f"vk vision unavailable ({e.__name__})",
                extra={"exception": e},
            )
            return resp_message_text, resp_attachments

    resp_message_text = ""
    resp_attachments = []
    for img in results:
        resp_message_text += "Изображение:\n"
        if len(img) == 0 or img[0].get("labels") is None:
            resp_message_text += "[Объекты не распознаны]\n"
        else:
            for obj in img[0]["labels"]:
                obj_name = obj["rus"]
                probability = obj["prob"] * 100
                obj_result = f"{probability:.2f}% - {obj_name}"
                if obj["rus_categories"]:
                    obj_result += f" {obj['rus_categories']}"
                obj_result += "\n"
                resp_message_text += obj_result
            resp_message_text += "\n"

    duration = time.perf_counter() - ts_start
    logger.debug(msg="end image processing", extra={"duration": duration})
    return resp_message_text, resp_attachments


command = command_system.Command(
    label="Распознавание изображений Mail Vision",
    command="command_graphic_vk",
    description="Это команда распознаёт объекты на изображении.",
    handler=command_handler,
    prompt_handler=prompt_handler,
)
