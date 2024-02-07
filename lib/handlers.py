import asyncio
import datetime
import re
from telebot.types import (CallbackQuery, ChatMemberUpdated, Message)

from lib.base import CustomBot
from lib.callback_texts import CALLBACK_TEXTS
from lib.states import States, QUESTION_MESSAGES
from lib.viewmodel import (get_user, add_new_chat_member, remove_chat_member,
                           get_user_wishes, get_group_participants, get_group_participants_list,
                           set_birthday, set_user_name_data, set_wishes,
                           make_user_wishes_btns_markup)

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


async def check_user_wishes(call: CallbackQuery, data, bot: CustomBot):
    payload = call.data[7:].strip()
    usr = await get_user_wishes(call.from_user.id, int(payload))
    if not usr:
        await bot.send_message(call.from_user.id, CALLBACK_TEXTS.wishes_unavailable)
    else:
        await bot.send_message(call.from_user.id, CALLBACK_TEXTS.wishes_of_user.format(
            f_name=usr.first_name, l_name=usr.last_name, wishes=usr.wish_string))


async def notext_input(message: Message, data, bot: CustomBot):
    await bot.reply_to(message, CALLBACK_TEXTS.incorrect_input)
    return


async def update_wishes(message: Message, data, bot: CustomBot):
    wishes = message.text
    try:
        await set_wishes(message.from_user.id, wishes)
    except Exception as e:
        await bot.reply_to(message, str(e))
        return
    await bot.delete_state(message.from_user.id, message.chat.id)
    await bot.reply_to(message, CALLBACK_TEXTS.wishes_updated)
    await bot.delete_message(message.chat.id, QUESTION_MESSAGES[message.chat.id].id)


async def update_birthday(message: Message, data, bot: CustomBot):
    try:
        birthday = datetime.date.fromisoformat(message.text)
    except ValueError:
        await bot.reply_to(message, CALLBACK_TEXTS.incorrect_birthday.format(text=message.text))
        return
    td = datetime.date.today()
    if birthday > td or (td - birthday).days // 365 > 100:
        await bot.reply_to(message, CALLBACK_TEXTS.incorrect_birthday.format(text=message.text))
        return
    await set_birthday(message.from_user.id, birthday)
    await bot.delete_state(message.from_user.id, message.chat.id)
    await bot.reply_to(message, CALLBACK_TEXTS.birthday_updated.format(birthday=str(birthday)))
    await bot.delete_message(message.chat.id, QUESTION_MESSAGES[message.chat.id].id)


async def notext_input(message: Message, data, bot: CustomBot):
    await bot.reply_to(message, CALLBACK_TEXTS.incorrect_input)


async def update_name(message: Message, data, bot: CustomBot):
    name_data = str(message.text).split(' ', 1)
    first_name, last_name = (name_data + [''])[:2]
    if not re.match(r'[\s\w]+', first_name) or (not re.match(r'[\s\w]+', last_name) and last_name):
        await bot.reply_to(message, CALLBACK_TEXTS.only_alpha)
        await bot.set_state(message.from_user.id, States.update_name, message.chat.id)
        return
    await set_user_name_data(first_name, last_name, message.from_user)
    await bot.delete_state(message.from_user.id, message.chat.id)
    await bot.reply_to(message, CALLBACK_TEXTS.name_has_been_changed.format(new_name=' '.join(name_data)))
    await bot.delete_message(message.chat.id, QUESTION_MESSAGES[message.chat.id].id)


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


async def user_wishes_keyboard_shift(call: CallbackQuery, data, bot: CustomBot):
    try:
        offset = int(call.data[16:])
    except:
        import traceback
        traceback.print_exc()
        return
    participants = await get_group_participants(call.chat.id)
    userids = [(i, m.id) for i, m in enumerate(participants)]
    markup = make_user_wishes_btns_markup(userids, offset)
    await bot.edit_message_reply_markup(call.chat.id, call.message.id, reply_markup=markup)



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


async def chat_members(call: CallbackQuery, data, bot: CustomBot):
    payload = call.data[13:].strip()
    chat = await bot.get_chat(int(payload))
    msg, userids = await get_group_participants_list(chat)
    markup = make_user_wishes_btns_markup(userids, 0)
    await bot.send_message(call.chat.id, msg, parse_mode='MarkdownV2', reply_markup=markup)
