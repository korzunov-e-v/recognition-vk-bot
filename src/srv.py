import asyncio
import logging
import sys

from src.config import service_settings
from src.modules.command_system import load_modules
from src.modules.vk.vk import start_polling
from src.utils import CustomJSONFormatter

logger = logging.getLogger("global_logger")
logger.setLevel(service_settings.log_level)

file_handler = logging.FileHandler(filename="vk-bot.log", encoding="utf-8")
stdout_handler = logging.StreamHandler(stream=sys.stdout)

json_formatter = CustomJSONFormatter()

file_handler.setFormatter(json_formatter)
stdout_handler.setFormatter(json_formatter)

logger.addHandler(file_handler)
logger.addHandler(stdout_handler)


async def main():
    load_modules()
    await start_polling()


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(main())
