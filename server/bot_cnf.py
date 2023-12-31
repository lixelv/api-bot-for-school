import aiogram
import requests

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from cnf import env, link

# db_url = f'mysql://{env("USER_")}:{env("PASSWORD_")}@{env("HOST_")}:{env("PORT_")}/{env("DB_")}?allowPublicKeyRetrieval=true'

token = env('TELEGRAM')

start_ = 'Привет, я бот созданный чтобы управлять \nкомпьютерами в *40 кабинете школы №358*\. \n\nЧтобы ознакомится с моим функционалом введите */help*'

help_ = """Этот бот создан для управления компьютерами в *40 кабинете 358 школы\.*

Для записи в бота команды используйте */program \(args\)*
Очень важно, что если у вашей команды есть аргументы типа ссылки при запуске браузера, то перечисляйте их через запятую с пробелом `(, )`

Для запуска программы на компьютерах введите */a*"""

bot = aiogram.Bot(token)
dp = aiogram.Dispatcher(bot)

def inline(lst: list | tuple, prefix) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=2)
    buttons = []
    for id_, name_ in lst:
        buttons.append(InlineKeyboardButton(name_, callback_data=f'{prefix}_{id_}'))

    if len(buttons) % 2 != 0:
        buttons.append(InlineKeyboardButton('\u200B', callback_data='@none'))

    kb.add(*buttons)
    kb.add(InlineKeyboardButton('Закрыть ❌', callback_data='close'))

    return kb

def send_update(mac, startup = False):
    json_data = {"data": startup, "mac": mac}
    requests.post(link+'update', json=json_data)

def get_websockets():
    return requests.get(link+'ping_websockets').json()["data"]

def get_macs(startup = False):
    if startup:
        json_data = {"data": "startup"}
    else:
        json_data = {"data": None}
        
    data = requests.get(link+'ping_macs', json=json_data).json()["data"]
    return [('all', 'all')] + data if data else None
