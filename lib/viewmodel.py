import datetime
from itertools import zip_longest
import os

from asyncache import cached
from cachetools import TTLCache
from sqlalchemy import update, func, and_, case, String, delete
from sqlalchemy.orm import aliased
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.future import select
from telebot.types import User as TelebotUser, InlineKeyboardMarkup, InlineKeyboardButton, Chat


from lib.callback_texts import CALLBACK_TEXTS
from models import Groups, Users


UserCache = TTLCache(1024, 60)
engine = create_async_engine(
    os.getenv('PG_URI_ASYNC'),
    echo=False
)
AsyncSession = async_sessionmaker(engine, expire_on_commit=False)


GENERATIVE_MONTHS = {
    1: 'января',
    2: 'февраля',
    3: 'марта',
    4: 'апреля',
    5: 'мая',
    6: 'июня',
    7: 'июля',
    8: 'августа',
    9: 'сентября',
    10: 'октября',
    11: 'ноября',
    12: 'декабря',
}


@cached(UserCache, lambda x: x.id)
async def get_user(user_payload: TelebotUser) -> Users:
    stmt = (
        insert(Users)
        .values(
            id=user_payload.id,
            username=user_payload.username if user_payload.username else '',
            first_name=user_payload.first_name if user_payload.first_name else '',
            last_name=user_payload.last_name if user_payload.last_name else ''
        )
    )
    stmt = (
        stmt.on_conflict_do_update(
            index_elements=[Users.id],
            set_=dict(username=stmt.excluded.username)
        )
        .returning(Users)
    )
    async with AsyncSession.begin() as session:
        q = await session.execute(stmt)
        user = q.scalar()
    return user


@cached(UserCache, lambda x: x)
async def get_user_by_id(id_: int) -> Users|None:
    req = select(Users).where(Users.id == id_)
    async with AsyncSession.begin() as session:
        q = await session.execute(req)
    return q.scalar()


async def set_user_name_data(name, surname, user_payload: TelebotUser) -> None:
    user = await get_user(user_payload)
    user_id = user.id
    naming_req = (
        update(Users)
        .where(Users.id == user_id)
        .values(
            first_name=name,
            last_name=surname,
        )
    )
    async with AsyncSession.begin() as session:
        await session.execute(naming_req)
    UserCache.clear()


async def get_user_info(user_payload: TelebotUser):
    user = await get_user(user_payload)
    req = (
        select(
            select(func.array_agg(Groups.id)).where(Groups.userid == user.id).scalar_subquery().label('groupids'),
            Users.first_name,
            Users.last_name,
            Users.username,
            Users.wish_string.label('my_wishes'),
            Users.birthday
        )
        .where(Users.id == user.id)
    )
    async with AsyncSession.begin() as session:
        q = await session.execute(req)
        data = q.one_or_none()
        if data is None:
            raise Exception(CALLBACK_TEXTS.database_error)
    return data


async def set_wishes(user_id: int, wishes: str):
    req = update(Users).where(Users.id == user_id).values(wish_string=wishes)
    async with AsyncSession.begin() as session:
        await session.execute(req)
    UserCache.clear()


async def set_birthday(user_id: int, birthday: datetime.date):
    req = update(Users).where(Users.id == user_id).values(birthday=birthday)
    async with AsyncSession.begin() as session:
        await session.execute(req)
    UserCache.clear()


async def get_members(user_payload: TelebotUser):
    user = await get_user(user_payload)
    if not user.groupid:
        m_str = CALLBACK_TEXTS.is_not_joined
    else:
        room_req = (
            select(
                func.row_number().over().label('rnum'),
                case((Users.birthday != None, Users.birthday.cast(String)), else_='').label('birthday'),
                Users.username,
                Users.first_name,
                Users.last_name,
            )
            .join(Groups, Groups.id == Users.groupid)
            .where(Groups.id == user.groupid)
            .order_by(Users.first_name, Users.last_name)
        )
        async with AsyncSession.begin() as session:
            q = await session.execute(room_req)
            members = q.all()
        m_str = '\n'.join([f'{m.rnum}. {m.birthday} @{m.username} {m.first_name} {m.last_name}' for m in members])
    return m_str


async def get_user_groups(userid: int) -> list[int]:
    req = select(Groups.id).where(Groups.userid == userid)
    async with AsyncSession.begin() as session:
        q = await session.execute(req)
    return q.scalars().all()


def get_word_plural_form(word_forms: tuple[str,str,str], number: int):
    match int(str(number)[-1]):
            case 1:
                return word_forms[0]
            case 2 | 3 | 4:
                return word_forms[1]
            case _:
                return word_forms[2]


def how_old(birthday: datetime.date) -> str:
    if not birthday:
        return ''
    td = datetime.date.today()
    if td.month > birthday.month or (td.month == birthday.month and td.day >= birthday.day):
        old = td.year - birthday.year
    else:
        old = td.year - birthday.year - 1
    ystr = get_word_plural_form(('год', 'года', 'лет'), old)
    return f'\({old} {ystr}\)'


def when_bd(birthday: datetime.date) -> str:
    if not birthday: return ''
    td = datetime.date.today()
    fbd = birthday.replace(year=td.year)
    if fbd < td:
        fbd = birthday.replace(year=td.year+1)
    days = (fbd - td).days
    bdstr = f'{birthday.day} {GENERATIVE_MONTHS[birthday.month]}'
    if days < 20:
        daystr = get_word_plural_form(('день', 'дня', 'дней'), days)
        return f'{bdstr} **осталось {days} {daystr} до ДР**'
    return bdstr


async def get_group_participants_list(chat) -> tuple[str, list[int]]:
    participants = await get_group_participants(chat.id)
    msg = CALLBACK_TEXTS.participants_header.format(groupname=chat.title)
    lst = [
        f'{i+1}\. @{m.username} {m.first_name} {m.last_name} {how_old(m.birthday)} {when_bd(m.birthday)} '
        for i, m in enumerate(participants)
    ]
    msg += '\n'.join(lst)
    msg += CALLBACK_TEXTS.to_check_wishes_press_a_btn
    return msg, [(i+1, m.id) for i, m in enumerate(participants)]


def make_user_wishes_btns_markup(
    userids: list[tuple[int, int]], groupid: int, offset: int=0) -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup()
    btns = []
    print(userids, offset)
    if len(userids) < 9:
        stop = len(userids)
        offset = 0
    elif offset:
        if len(userids[offset:]) > 7:
            stop = offset + 6
        else:
            stop = offset + 7
    else:
        if len(userids) > 8:
            stop = offset + 7
        else:
            stop = offset + 8
    if offset:
        btns.append(InlineKeyboardButton(text='<<', callback_data=f'inline_keyboard {groupid} {max(offset-1, 0)}'))
    for number, userid in userids[offset: stop]:
        btns.append(InlineKeyboardButton(text=number, callback_data=f'wishes {userid}'))
    if stop < len(userids):
        btns.append(InlineKeyboardButton(text='>>', callback_data=f'inline_keyboard {groupid} {min(offset+1, len(userids))}'))
    markup.add(*btns)
    return markup


def make_chats_markup(chats: Chat) -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup()
    chbutns = (
        InlineKeyboardButton(text=ch.title, callback_data=f'chat_members {ch.id}')
        for ch in chats
    )
    for chline in zip_longest(*[chbutns] * 2):
        markup.add(*chline)
    return markup


async def get_user_wishes(askerid: int, userid: int) -> Users|None:
    asker = aliased(Users)
    user = aliased(Users)
    req = (
        select(user)
        .select_from(asker)
        .join(Groups, Groups.userid == asker.id)
        .join(user, Groups.userid == user.id)
        .where(asker.id == askerid, user.id == userid)
    )
    async with AsyncSession.begin() as session:
        q = await session.execute(req)
    return q.scalar()


async def get_group_participants(chatid: int) -> list[Users]:
    req = select(Users).select_from(Groups).join(
        Users, Groups.userid == Users.id).where(
        Groups.id == chatid).order_by(Users.birthday)
    async with AsyncSession.begin() as session:
        q = await session.execute(req)
    return q.scalars().all()


async def add_new_chat_member(userid: int, chatid: int):
    req = insert(Groups).values(id=chatid, userid=userid)
    req = req.on_conflict_do_nothing(index_elements=['id', 'userid'])
    async with AsyncSession.begin() as session:
        q = await session.execute(req)


async def remove_chat_member(userid: int, chatid: int):
    req = delete(Groups).where(Groups.id == chatid, Groups.userid == userid)
    async with AsyncSession.begin() as session:
        q = await session.execute(req)
