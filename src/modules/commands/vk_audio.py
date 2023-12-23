import logging
import os
import time

import aiohttp
from aiohttp import ClientConnectorError

from src.modules import command_system
from src.modules.vk_audio import recognize_audio_file

logger = logging.getLogger("global_logger")


async def _download_audio_message(audio_message_link: str) -> str:
    ts_start = time.perf_counter()
    logger.debug("downloading audio-message")
    async with aiohttp.ClientSession() as session:
        async with session.get(audio_message_link) as resp:
            data = await resp.content.read()
            filename = audio_message_link.split("/")[-1]
            temp_dir_name = "tmp"
            os.makedirs(temp_dir_name, exist_ok=True)
            file_path = os.path.join(temp_dir_name, filename)
            with open(file_path, "wb") as f:
                f.write(data)
    duration = time.perf_counter() - ts_start
    file_size = os.stat(file_path).st_size
    logger.debug(
        msg="downloading audio-message complete",
        extra={"duration": duration, "size_bytes": file_size},
    )
    return file_path


def prompt_handler():
    message = "Отправьте голосовое сообщение для распознавания"
    attachments = []
    return message, attachments


async def command_handler(user_message: str, user_attachments: list):
    resp_message_text = "Голосового сообщения не было"
    resp_attachments = []
    user_audio_attachments = [
        att["audio_message"]["link_ogg"] for att in user_attachments if att["type"] == "audio_message"
    ]
    if user_audio_attachments:
        ts_start = time.perf_counter()
        logger.debug("start audio processing")
        logger.debug("start VK Audio processing")

        audio_file_path = await _download_audio_message(user_audio_attachments[0])
        try:
            resp_message_text = await recognize_audio_file(audio_file_path)
        except ClientConnectorError:
            resp_message_text = "[ошибка подключения к API VK, повторите попытку]"

        duration = time.perf_counter() - ts_start
        logger.debug(msg="end VK Audio processing", extra={"duration": duration})

        if resp_message_text == "":
            resp_message_text = "[тишина]"

        os.remove(audio_file_path)
    return resp_message_text, resp_attachments


command = command_system.Command(
    label="Распознавание речи от VK",
    command="command_audio_vk",
    description="Это команда переводит аудиосообщение в текст.",
    handler=command_handler,
    prompt_handler=prompt_handler,
)
