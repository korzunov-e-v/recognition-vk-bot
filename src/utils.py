import functools
import logging
import time
from datetime import datetime

from json_log_formatter import JSONFormatter, _json_serializable
from vk_api.bot_longpoll import VkBotEvent


class CustomJSONFormatter(JSONFormatter):
    def to_json(self, record):
        try:
            return self.json_lib.dumps(record, ensure_ascii=False, default=_json_serializable)
        except (TypeError, ValueError, OverflowError):
            try:
                return self.json_lib.dumps(record)
            except (TypeError, ValueError, OverflowError):
                return "{}"

    def json_record(self, message, extra, record):
        result = {}
        if "time" not in extra:
            result["time"] = datetime.utcnow()
        result["levelname"] = record.levelname
        result["message"] = message
        result.update(extra)
        if record.exc_info:
            result["exc_info"] = self.formatException(record.exc_info)
        return result


def log_for_handler_decorator(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        logger = logging.getLogger("global_logger")
        ts_start = time.perf_counter()
        resp_message_text, resp_attachments = await func(*args, **kwargs)
        duration = time.perf_counter() - ts_start

        event: VkBotEvent = kwargs.get("event") or args[0]
        request_attachments = event.message.attachments
        req_audios = [att["audio_message"]["link_ogg"] for att in request_attachments if att["type"] == "audio_message"]
        req_photos = [
            max(att["photo"]["sizes"], key=lambda a: a["height"])["url"]
            for att in request_attachments
            if att["type"] == "photo"
        ]
        request_attachments_urls = req_photos + req_audios
        logger.info(
            msg="Message sent",
            extra={
                "req_chat_id": event.message.peer_id,
                "req_user_id": event.message.from_id,
                "req_message": event.message.text,
                "req_attachments": request_attachments_urls,
                "resp_message": resp_message_text,
                "resp_attachments": resp_attachments,
                "resp_time": duration,
            },
        )

    return wrapper
