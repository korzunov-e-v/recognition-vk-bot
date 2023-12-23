import json
import logging

from vk_api import VkApi, VkUpload
from vk_api.bot_longpoll import VkBotEventType, VkBotLongPoll
from vk_api.utils import get_random_id

from src.config import service_settings
from src.modules.command_system import command_map, get_all_keyboards
from src.utils import log_for_handler_decorator

logger = logging.getLogger("global_logger")


class VkDirectFlow:
    def __init__(self, vk: VkApi):
        self.vk = vk
        self._api = vk.get_api()
        self._upload = VkUpload(vk=vk)
        self.long_poll = VkBotLongPoll(vk=self.vk, group_id=service_settings.group_id)

    async def polling(self):
        logger.debug("polling started")
        for event in self.long_poll.listen():
            logger.debug(f"new event {event.type.value}")
            if event.type == VkBotEventType.MESSAGE_NEW:
                await self._process_message(event=event)

    @log_for_handler_decorator
    async def _process_message(self, event) -> tuple[str, list]:
        random_id = get_random_id()
        user_id = event.message.from_id
        request_message = event.message.text
        request_attachments = event.message.attachments
        req_audios = [att["audio_message"]["link_ogg"] for att in request_attachments if att["type"] == "audio_message"]
        req_photos = [
            max(att["photo"]["sizes"], key=lambda a: a["height"])["url"]
            for att in request_attachments
            if att["type"] == "photo"
        ]

        message = "Отправьте голосовое сообщение для распознавания речи или изображение для распознавания объектов"
        attachments = []

        if request_message == "/logs":
            log_file_name = "vk-bot.log"
            doc = self._upload.document_message(doc=log_file_name, peer_id=user_id)
            document_name = f"{doc['type']}{doc['doc']['owner_id']}_{doc['doc']['id']}"
            message, attachments = "Логи сервиса", [document_name]
        elif req_audios:
            command_class = command_map["command_audio_vk"]
            message, attachments = await command_class.process(
                user_message=request_message,
                user_attachments=request_attachments,
            )
        elif req_photos:
            command_class = command_map["command_graphic_vk"]
            message, attachments = await command_class.process(
                user_message=request_message,
                user_attachments=request_attachments,
            )

        self._api.messages.send(
            peer_id=event.message.peer_id,
            message=message,
            attachment=attachments,
            random_id=random_id,
            keyboard=[],
        )
        return message, attachments


class VkButtonFlow:
    def __init__(self, vk: VkApi):
        self.vk = vk
        self._api = vk.get_api()
        self._upload = VkUpload(vk=vk)
        self.long_poll = VkBotLongPoll(vk=self.vk, group_id=service_settings.group_id)
        self._user_states = {}

    async def polling(self) -> None:
        logger.debug("polling started")
        for event in self.long_poll.listen():
            logger.debug(f"new event {event.type.value}")
            if event.type == VkBotEventType.MESSAGE_NEW:
                if event.message.payload:
                    await self._process_button(event=event)
                else:
                    await self._process_message(event=event)

    @log_for_handler_decorator
    async def _process_button(self, event) -> tuple[str, list]:
        user_id = event.message.from_id
        payload = json.loads(event.message.payload)
        command = payload["command"]
        keyboards = get_all_keyboards()
        random_id = get_random_id()

        logger.info(
            msg="New command",
            extra={"user_id": user_id, "command": command},
        )
        if command == "cancel":
            try:
                del self._user_states[user_id]
            except KeyError:
                pass
            message, attachments, keyboard = "Выберите команду на клавиатуре в приложении", [], keyboards["main"]
        else:
            command_class = command_map.get(command, None)
            if command_class is None:
                logger.warning(
                    msg="command not found",
                    extra={"user_id": user_id, "command": command},
                )
                message, attachments, keyboard = "Команда не распознана", [], keyboards["main"]
            else:
                message, attachments = await command_class.get_prompt()
                keyboard = keyboards["cancel"]
                self._user_states[user_id] = command
        self._api.messages.send(
            peer_id=event.message.peer_id,
            message=message,
            attachments=attachments,
            random_id=random_id,
            keyboard=keyboard,
        )
        return message, attachments

    @log_for_handler_decorator
    async def _process_message(self, event) -> tuple[str, list]:
        random_id = get_random_id()
        keyboards = get_all_keyboards()
        user_id = event.message.from_id
        request_message = event.message.text
        request_attachments = event.message.attachments

        message = "Выберите команду на клавиатуре в приложении"
        attachments = []

        if request_message == "/logs":
            log_file_name = "vk-bot.log"
            doc = self._upload.document_message(doc=log_file_name, peer_id=user_id)
            document_name = f"{doc['type']}{doc['doc']['owner_id']}_{doc['doc']['id']}"
            message, attachments = "Логи сервиса", [document_name]

        state = self._user_states.get(user_id, None)
        if state and state != "info":
            command_class = command_map[state]
            message, attachments = await command_class.process(
                user_message=request_message,
                user_attachments=request_attachments,
            )

        self._api.messages.send(
            peer_id=event.message.peer_id,
            message=message,
            attachment=attachments,
            random_id=random_id,
            keyboard=keyboards["main"],
        )
        return message, attachments
