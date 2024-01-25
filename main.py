import asyncio
from functools import partial
import os

from telebot import asyncio_filters
from telebot.asyncio_storage import StateMemoryStorage

from lib.base import CustomBot
from lib.buttons import UserButtonSet
from lib.handlers import (callback_query, update_birthday, user_come, user_go,
                            my_chats_updated, start,
                          update_name, update_wishes)
from lib.states import States


TOKEN = os.getenv('TOKEN')

bot = CustomBot(TOKEN, state_storage=StateMemoryStorage())
bot.add_custom_filter(asyncio_filters.StateFilter(bot))
bot.add_button_set(UserButtonSet)

bot.message_handler(commands=['start'])(start)
bot.message_handler(state=States.update_name)(update_name)
bot.message_handler(state=States.update_wishes)(update_wishes)
bot.callback_query_handler(
    func=lambda call: call.data in ('change_name', 'set_wishes', 'set_birthday', 'cancel')
)(callback_query)
bot.message_handler(state=States.update_birthday)(update_birthday)
bot.my_chat_member_handler(lambda x: True)(partial(my_chats_updated, bot=bot))
bot.message_handler(content_types=['new_chat_members'])(user_come)
bot.message_handler(content_types=['left_chat_member'])(user_go)


if __name__ == '__main__':
    asyncio.run(bot.polling())
