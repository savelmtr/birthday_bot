from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from lib.base import AbstractButton, AbstractButtonSet, CustomBot
from lib.viewmodel import (get_user_groups, get_user_info, get_group_participants_list, make_user_wishes_btns_markup)
from lib.callback_texts import CALLBACK_TEXTS
import asyncio
from lib.states import States, QUESTION_MESSAGES


CANCEL_MARKUP = InlineKeyboardMarkup()
CANCEL_MARKUP.add(InlineKeyboardButton(text='Отмена', callback_data='cancel'))


class GetTeamMates(AbstractButton):
    name = 'Участники групп 👥'

    async def run(self, message: Message):
        groupids = await get_user_groups(message.from_user.id)
        me = await self.bot.get_me()
        markup = None
        match len(groupids):
            case 0:
                msg = CALLBACK_TEXTS.you_participate_no_groups
            case 1:
                chat = await self.bot.get_chat(groupids[0])
                msg, userids = await get_group_participants_list(chat, me)
                markup = make_user_wishes_btns_markup(userids, 0)
            case 3:
                chats = await asyncio.gather(*[self.bot.get_chat(gid) for gid in groupids])
                chats = sorted(chats, key=lambda c: c.title)
                lst = [
                    f'{i}. {chat.title} https://t.me/{me.username}/?participants={chat.id}'
                    for i, chat in enumerate(chats)
                ]
                msg = CALLBACK_TEXTS.choose_chat + '\n'.join(lst)
        await self.bot.send_message(message.chat.id, msg, parse_mode='MarkdownV2', reply_markup=markup)


class GetMyData(AbstractButton):
    name = 'Мои данные 📋'

    async def get_groupnames(self, groupids: list[int]):
        chats = await asyncio.gather(*[
            self.bot.get_chat(gid)
            for gid in groupids
        ])
        names = [c.title for c in chats]
        return ', '.join(names)

    async def run(self, message: Message):
        bot_info = await self.bot.get_me()
        data = await get_user_info(message.from_user)
        msgs = []
        for kwargs, callback_text in (
            ({'groups': await self.get_groupnames(data.groupids)}, CALLBACK_TEXTS.info_in_group),
            ({'my_wishes': data.my_wishes}, CALLBACK_TEXTS.info_wishes),
            ({'username': data.username, 'first_name': data.first_name, 'last_name':data.last_name}, CALLBACK_TEXTS.info_name),
            ({'birthday': data.birthday}, CALLBACK_TEXTS.my_birthday)
        ):
            if any(kwargs.values()):
                msgs.append(callback_text.format(**kwargs))
        msg = '\n'.join(msgs)
        await self.bot.send_message(message.chat.id, msg)


class ChangeMyName(AbstractButton):
    name = 'Изменить имя ✍'

    async def run(self, message: Message):
        QUESTION_MESSAGES[message.chat.id] = await self.bot.send_message(
            message.chat.id,
            CALLBACK_TEXTS.change_name_proposal,
            reply_markup=CANCEL_MARKUP
        )
        await self.bot.set_state(message.from_user.id, States.update_name, message.chat.id)


class ChangeWishes(AbstractButton):
    name = 'Изменить пожелания и интересы 🎀'

    async def run(self, message: Message):
        QUESTION_MESSAGES[message.chat.id] = await self.bot.send_message(
            message.chat.id,
            CALLBACK_TEXTS.change_wishes_proposal,
            reply_markup=CANCEL_MARKUP
        )
        await self.bot.set_state(message.from_user.id, States.update_wishes, message.chat.id)


class ChangeBirthday(AbstractButton):
    name = 'Установить дату дня рождения 👶'

    async def run(self, message: Message):
        QUESTION_MESSAGES[message.chat.id] = await self.bot.send_message(
            message.chat.id,
            CALLBACK_TEXTS.set_birthday_proposal,
            reply_markup=CANCEL_MARKUP
        )
        await self.bot.set_state(message.from_user.id, States.update_birthday, message.chat.id)


class UserButtonSet(AbstractButtonSet):
    buttons = (
        (GetTeamMates, GetMyData),
        (ChangeMyName, ChangeWishes),
        (ChangeBirthday, )
    )

    async def is_available(self, bot: CustomBot, chat_id: int | str):
        chat = await bot.get_chat(chat_id)
        return chat.type == 'private'
