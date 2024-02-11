import asyncio
import croniter
import datetime
from lib.base import CustomBot
from lib.viewmodel import get_participants_by_birthday, when_bd_days, how_old, how_old_str
from lib.callback_texts import CALLBACK_TEXTS, GENERATIVE_MONTHS, NOMINATIVE_MONTHS
import traceback


STARTING_POINT = datetime.datetime.utcnow() - datetime.timedelta(hours=2)


async def tasks_manager(bot: CustomBot, tasks: tuple[dict]):
    for ts in tasks:
        ts['iterator'] = croniter.croniter(ts['cronstr'], STARTING_POINT)
        ts['next_ft'] = ts['iterator'].get_next(datetime.datetime)
    while True:
        now = datetime.datetime.utcnow()
        for ts in tasks:
            try:
                if now >= ts['next_ft']:
                    await ts['coro'](bot)
                    ts['next_ft'] = ts['iterator'].get_next(datetime.datetime)
            except:
                traceback.print_exc()
        await asyncio.sleep(1)


async def monthly(bot: CustomBot):
    month = datetime.date.today().month
    month = month + 1 if month < 12 else 1
    participants = await get_participants_by_birthday(month)
    groups = {p['groupid'] for p in participants}
    header = CALLBACK_TEXTS.notice_header.format(month=NOMINATIVE_MONTHS[month]).capitalize()
    for gid in groups:
        birthday_boys = []
        ps = sorted([p for p in participants if p['groupid'] == gid], key=lambda u: when_bd_days(u['birthday']))
        for p in ps:
            birthday_boys.append(
                f'🎉 {p["first_name"]} {p["last_name"]} {p["birthday"].day} '\
                f'{GENERATIVE_MONTHS[p["birthday"].month]}, {how_old_str(how_old(p["birthday"]) + 1)}')
        birthday_boys_list = '\n'.join(birthday_boys)
        await bot.send_message(gid, header + birthday_boys_list)


async def congrats(bot: CustomBot):
    today = datetime.date.today()
    participants = await get_participants_by_birthday(today.month, today.day)
    groups = {p['groupid'] for p in participants}
    for gid in groups:
        birthday_boys = []
        ps = [p for p in participants if p['groupid'] == gid]
        if len(ps) > 1:
            header = CALLBACK_TEXTS.congrats_header_plural
            bullet = '🎉 '
        else:
            header = CALLBACK_TEXTS.congrats_header
            bullet = ''
        for p in ps:
            birthday_boys.append(
                f'{bullet}{p["first_name"]} {p["last_name"]} {how_old_str(how_old(p["birthday"]))}')
        birthday_boys_list = '\n'.join(birthday_boys)
        await bot.send_message(gid, header + birthday_boys_list)
