from src.modules import command_system


def prompt_handler():
    message = ""
    attachments = []
    command_list = list(command_system.command_map.keys())
    command_list.remove("info")
    for command_name in command_list:
        command = command_system.command_map[command_name]
        message += command.label + " - " + command.description + "\n\n"
    return message, attachments


async def command_handler(user_message: str, user_attachments: list):
    resp_message = ""
    resp_attachments = []
    return resp_message, resp_attachments


info_command = command_system.Command(
    label="Информация о командах",
    command="info",
    description="Выводит список команд и их описание.",
    handler=command_handler,
    prompt_handler=prompt_handler,
)
