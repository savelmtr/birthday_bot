from telebot.asyncio_handler_backends import State, StatesGroup


class States(StatesGroup):
    update_birthday = State()
    update_name = State()
    update_wishes = State()
