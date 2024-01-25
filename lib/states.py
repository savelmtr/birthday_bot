from telebot.asyncio_handler_backends import State, StatesGroup


class States(StatesGroup):
    welcome_workflow = State()
    update_birthday = State()
    join_group = State()
    create_group = State()
    wish_list = State()
    update_name = State()
    update_wishes = State()
    create_password = State()
    enter_password = State()
    max_price = State()
    rename = State()
