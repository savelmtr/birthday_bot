import datetime
from telebot.types import (CallbackQuery, InlineKeyboardButton, ChatMemberUpdated,
                           InlineKeyboardMarkup, Message)

from lib.base import CustomBot
from lib.callback_texts import CALLBACK_TEXTS
from lib.states import States
from lib.viewmodel import (get_user, add_new_chat_member, remove_chat_member,
                           set_birthday, set_user_name_data, set_wishes)

from lib.buttons import ChangeWishes, ChangeMyName, ChangeBirthday


async def start(message: Message, data, bot: CustomBot):
    payload = message.text[6:].strip()
    if not payload:
        await bot.reply_to(message, CALLBACK_TEXTS.welcome)
    else:
        user = await get_user(message.from_user)
        try:
            groupid = int(payload)
        except ValueError:
            await bot.send_message(message.chat.id, CALLBACK_TEXTS.groupid_incorrect.format(payload=payload))
            return
        await add_new_chat_member(user.id, groupid)
        chat = await bot.get_chat(groupid)
        await bot.send_message(
            message.chat.id,
            CALLBACK_TEXTS.you_ware_added_as_memeber_of_group.format(chatname=chat.title)
        )


async def update_wishes(message: Message, data, bot: CustomBot):
    wishes = message.text
    try:
        await set_wishes(message.from_user.id, wishes)
    except Exception as e:
        await bot.reply_to(message, str(e))
        return
    await bot.delete_state(message.from_user.id, message.chat.id)
    await bot.reply_to(message, CALLBACK_TEXTS.wishes_updated)


async def update_birthday(message: Message, data, bot: CustomBot):
    try:
        birthday = datetime.date.fromisoformat(message.text)
    except ValueError:
        await bot.reply_to(message, CALLBACK_TEXTS.incorrect_birthday(text=message.text))
        return
    await set_birthday(message.from_user.id, birthday)
    await bot.delete_state(message.from_user.id, message.chat.id)
    await bot.reply_to(message, CALLBACK_TEXTS.birthday_updated.format(birthday=str(birthday)))


async def update_name(message: Message, data, bot: CustomBot):
    name_data = str(message.text).split(' ', 1)
    first_name, last_name = (name_data + [''])[:2]
    if not first_name.isalpha() or (not last_name.isalpha() and last_name):
        await bot.reply_to(message, 'Назовите себя, используя только буквы 😀')
        await bot.set_state(message.from_user.id, States.update_name, message.chat.id)
        return
    await set_user_name_data(first_name, last_name, message.from_user)
    await bot.delete_state(message.from_user.id, message.chat.id)
    await bot.reply_to(message, CALLBACK_TEXTS.name_has_been_changed.format(new_name=' '.join(name_data)))


def get_name_wishes_markup():
    change_name_btn = InlineKeyboardButton(text='Как меня зовут', callback_data='change_name')
    set_wishes_btn = InlineKeyboardButton(text='Мои интересы и пожелания', callback_data='set_wishes')
    birthday_btn = InlineKeyboardButton(text='Когда мой день рождения', callback_data='set_birthday')
    markup = InlineKeyboardMarkup()
    markup.add(change_name_btn)
    markup.add(set_wishes_btn)
    markup.add(birthday_btn)
    return markup


async def callback_query(call: CallbackQuery, data, bot: CustomBot):
    req = call.data
    call.message.from_user = call.from_user
    match req:
        case 'change_name':
            await ChangeMyName(bot).run(call.message)
        case 'set_wishes':
            await ChangeWishes(bot).run(call.message)
        case 'set_birthday':
            await ChangeBirthday(bot).run(call.message)
        case 'cancel':
            await bot.delete_state(call.from_user.id, call.from_user.id)
            await bot.delete_message(call.from_user.id, call.message.id)
            await bot.send_message(call.from_user.id, CALLBACK_TEXTS.cancel_successfull)


async def my_chats_updated(chat_updated: ChatMemberUpdated, bot: CustomBot):
    status = chat_updated.new_chat_member.status
    if status == 'member':
        bot_info = await bot.get_me()
        await bot.send_message(chat_updated.chat.id, CALLBACK_TEXTS.adder_link.format(
            bot_name=bot_info.username, chatid=chat_updated.chat.id))
    else:
        print(status)


async def user_come(message: Message, data, bot: CustomBot):
    bot_info = await bot.get_me()
    for member in message.new_chat_members:
        if bot_info.id !=member.id:
            user = await get_user(member)
            await add_new_chat_member(user.id, message.chat.id)


async def user_go(message: Message, data, bot: CustomBot):
    await remove_chat_member(message.left_chat_member.id, message.chat.id)
