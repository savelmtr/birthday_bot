import asyncio
from functools import partial
import os

from telebot import asyncio_filters
from telebot.asyncio_storage import StateMemoryStorage

from lib.base import CustomBot
from lib.buttons import UserButtonSet
from lib.handlers import (callback_query, update_birthday, user_come, user_go, user_wishes_keyboard_shift,
                            my_chats_updated, start, check_user_wishes, notext_input, chat_members,
                          update_name, update_wishes)
from lib.states import States
from lib.tasks import tasks_manager, monthly, congrats


TOKEN = os.getenv('TOKEN')

bot = CustomBot(TOKEN, state_storage=StateMemoryStorage())
bot.add_custom_filter(asyncio_filters.StateFilter(bot))
bot.add_button_set(UserButtonSet)

bot.message_handler(
    func=lambda m: True, content_types=['audio', 'photo', 'voice', 'video', 'document', 'location', 'contact', 'sticker']
)(notext_input)
bot.message_handler(commands=['start'])(start)
bot.callback_query_handler(func=lambda call: call.data.startswith('wishes'))(check_user_wishes)
bot.callback_query_handler(func=lambda call: call.data.startswith('inline_keyboard'))(user_wishes_keyboard_shift)
bot.callback_query_handler(func=lambda call: call.data.startswith('chat_members'))(chat_members)
bot.message_handler(state=States.update_name, content_types=['text'])(update_name)
bot.message_handler(state=States.update_wishes, content_types=['text'])(update_wishes)
bot.callback_query_handler(
    func=lambda call: call.data in ('change_name', 'set_wishes', 'set_birthday', 'cancel')
)(callback_query)
bot.message_handler(state=States.update_birthday, content_types=['text'])(update_birthday)
bot.my_chat_member_handler(lambda x: True)(partial(my_chats_updated, bot=bot))
bot.message_handler(content_types=['new_chat_members'])(user_come)
bot.message_handler(content_types=['left_chat_member'])(user_go)


TASKS = (
    {'cronstr': '18 20 8 * *', 'coro': monthly, 'iterator': None, 'next_ft': None},
    {'cronstr': '18 20 * * *', 'coro': congrats, 'iterator': None, 'next_ft': None},
)


async def main():
    task = asyncio.create_task(tasks_manager(bot, TASKS))
    await bot.polling()


if __name__ == '__main__':
    asyncio.run(main())
