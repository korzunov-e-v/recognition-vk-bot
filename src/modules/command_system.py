import importlib
import os
from typing import Callable

from vk_api.keyboard import VkKeyboard, VkKeyboardColor


class Command:
    def __init__(
        self,
        label: str,
        command: str,
        description: str,
        handler: Callable,
        prompt_handler: Callable,
    ):
        self.label = label
        self.command = command
        self.description = description
        self.handler = handler
        self.prompt_handler = prompt_handler
        command_map[command] = self

    async def process(self, user_message: str, user_attachments: list) -> tuple[str, list]:
        return await self.handler(user_message, user_attachments)

    async def get_prompt(self) -> tuple[str, list]:
        return self.prompt_handler()


def get_all_keyboards() -> dict[str, VkKeyboard]:
    keyboards = {}

    kb_cancel = VkKeyboard(one_time=True)
    kb_cancel.add_button(label="Отмена", color=VkKeyboardColor.NEGATIVE, payload={"command": "cancel"})
    keyboard_cancel = kb_cancel.get_keyboard()
    keyboards["cancel"] = keyboard_cancel

    kb_main = VkKeyboard(one_time=True)
    commands_keys = list(command_map.keys())
    commands_keys.remove("info")
    sorted_commands_keys = sorted(commands_keys)
    i = 0
    for command_key in sorted_commands_keys:
        i += 1
        command = command_map[command_key]
        kb_main.add_button(
            label=command.label,
            color=VkKeyboardColor.SECONDARY,
            payload={"command": command.command},
        )
        if i == 2:
            i = 0
            kb_main.add_line()
    info_command = command_map["info"]
    kb_main.add_button(
        label=info_command.label,
        color=VkKeyboardColor.PRIMARY,
        payload={"command": info_command.command},
    )
    keyboard_main = kb_main.get_keyboard()
    keyboards["main"] = keyboard_main

    return keyboards


def load_modules() -> None:
    files = os.listdir("src/modules/commands")
    modules = filter(lambda x: x.endswith(".py"), files)
    for m in modules:
        importlib.import_module("src.modules.commands." + m[0:-3])


command_map: dict[str, Command] = {}
