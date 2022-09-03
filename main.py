import asyncio
import datetime
import json
import logging
from time import sleep
import sqlite3

import bs4
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils import executor
import keyboards as kb
import config

API_TOKEN = config.auth_token  # Токен бота

session = requests.Session()
# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

"""generate keyboard with buttons"""


def decode_error_types(string):
    error_types = {'Критическая тревога ': '1',
                   'Сигнал тревоги ': '2',
                   'Сигнал для привлечения внимания ': '3',
                   'Доклад ': '4',
                   'Сигнал тревоги по ритму ': '5'}
    return error_types[string]


"""
Критическая тревога 
Сигнал тревоги 
Сигнал для привлечения внимания 
Доклад 
Сигнал тревоги по ритму 
"""


def get_users():
    with open('users.json') as file:
        try:
            u_list = json.load(file)
        except json.decoder.JSONDecodeError:
            u_list = []
    return u_list


def check_user_session():
    global session
    headers = {'Content-Type': 'application/json; charset=utf-8'}
    response = session.post(config.server + '/T4C/Content/StartPage.aspx/JsonCheckUserSession', headers=headers,
                            json={})

    return response.status_code


def get_failed_cows(group_id=''):
    response = session.get(config.server + '/xlink/ReportTable.aspx?id=10763&ALAN=18&LDN=group_id')
    soap = bs4.BeautifulSoup(response.text, 'html.parser')
    table = soap.find_all('table', {'class': 'xlink'})[0]
    rows = table.find_all('tr')
    failed_cows = ''
    for row in rows:
        cells = row.find_all('td')
        if len(cells) > 0:
            failed_cows += f"{cells[0].text} {cells[1].text} {cells[4].text} {cells[5].text} {cells[11].text} {cells[14].text}\n"

    return failed_cows


def get_errors_from_server(error_type='', device_address='', error_code='', page=1,
                           date_from='') -> list:
    with open('errors.json') as file:
        try:
            errors = json.load(file)
        except json.decoder.JSONDecodeError:
            errors = []
    new_errors = []
    params = {'Module': 53,
              'PageNo': page,
              'MaxParams': 9,
              '0': 2,
              '1': 1,
              '2': device_address,
              'Multisort': '2:1:1|',
              '4': date_from,
              '5': error_type,
              '8': '1,0,1'}
    print(date_from)
    headers = {'Content-Type': 'application/json'}

    url = config.server + '/T4C/Content/AjaxRequest.aspx'
    while True:
        response = session.post(url, headers=headers, params=params)
        if response.status_code == 200:
            break
        else:
            sleep(5)

    soup = bs4.BeautifulSoup(response.text, 'html.parser')
    table = soup.find_all('table')
    rows = table[0].find_all('tr')

    for row in rows:
        cells = row.find_all('td')
        if len(cells) > 0:
            new_error = {'device_address': cells[0].text,
                         'date': cells[2].text,
                         'type': cells[3].text,
                         'code': cells[4].text,
                         'description': cells[5].text}
            if new_error in errors:
                continue
            else:
                errors.append(new_error)
                new_errors.append(new_error)
    with open('errors.json', 'w') as file:
        json.dump(errors, file)

    return new_errors


def login():
    global session
    """Login to .net server T4C"""
    values = dict(txtUserName=config.username,
                  txtPassword=config.password,
                  btnLogin_5='Login',
                  __EVENTARGUMENT='',
                  __EVENTTARGET=''
                  )

    response = session.post(config.server + "/T4C/Content/Login.aspx", data=values)
    logging.info(response.status_code)


async def get_new_errors():
    while True:

        if check_user_session() != 200:
            print('relogin :(')
            login()
        users = get_users()
        new_errors = get_errors_from_server(date_from=str(datetime.date.today()))
        if len(new_errors) >= 1:
            for user in users:
                message = ''
                for error in new_errors:
                    if decode_error_types(error['type']) in user['sub_types']:
                        message += f"{error['date']} {error['device_address']} {error['code']} {error['description']}\n"
                if message != '':
                    """chunk message to avoid telegram error"""
                    for i in range(0, len(message), 4096):
                        await bot.send_message(user['user_id'], message[i:i + 4096], disable_notification=True)
        await asyncio.sleep(10)


@dp.message_handler(commands=['start', 'exit'])
async def send_welcome(message: types.Message):
    await message.answer("Привет! Я бот для отправки сообщений о проблемах на сервере T4C.", reply_markup=kb.main_menu())
    """save user id to users.json if not exists"""
    users = get_users()
    if message.chat.id not in [user['user_id'] for user in users]:
        users.append({'user_id': message.chat.id, 'sub_types': []})
        with open('users.json', 'w') as file:
            json.dump(users, file)


@dp.message_handler(commands=['1'])
async def subscribe_to_type_1(message: types.Message):
    users = get_users()
    for user in users:
        if user['user_id'] == message.chat.id:
            if '1' not in user['sub_types']:
                user['sub_types'].append('1')
                await message.answer("Ты подписан на уведомления о критических тревогах ✅")
            else:
                user['sub_types'].remove('1')
                await message.answer("Ты отписан от уведомлений о критических тревогах ❎")
            with open('users.json', 'w') as file:
                json.dump(users, file)


@dp.message_handler(commands=['2'])
async def subscribe_to_type_2(message: types.Message):
    users = get_users()
    for user in users:
        if user['user_id'] == message.chat.id:
            if '2' not in user['sub_types']:
                user['sub_types'].append('2')
                await message.answer("Ты подписан на сигнал тревоги 🚨")
            else:
                user['sub_types'].remove('2')
                await message.answer("Ты отписан от сигнала тревоги 🚨")
            with open('users.json', 'w') as file:
                json.dump(users, file)


@dp.message_handler(commands=['3'])
async def subscribe_to_type_3(message: types.Message):
    users = get_users()
    for user in users:
        if user['user_id'] == message.chat.id:
            if '3' not in user['sub_types']:
                user['sub_types'].append('3')

                await message.answer("Ты подписан на сигнал для привлечения внимания 🚨")
            else:
                user['sub_types'].remove('3')
                await message.answer("Ты отписан от сигнала для привлечения внимания 🚨")
            with open('users.json', 'w') as file:
                json.dump(users, file)


@dp.message_handler(commands=['4'])
async def subscribe_to_type_4(message: types.Message):
    users = get_users()
    for user in users:
        if user['user_id'] == message.chat.id:
            if '4' not in user['sub_types']:
                user['sub_types'].append('4')

                await message.answer("Ты подписан на доклады 📑")
            else:
                user['sub_types'].remove('4')
                await message.answer("Ты отписан от докладов 📑")
            with open('users.json', 'w') as file:
                json.dump(users, file)


@dp.message_handler(commands=['5'])
async def subscribe_to_type_5(message: types.Message):
    users = get_users()
    for user in users:
        if user['user_id'] == message.chat.id:
            if '5' not in user['sub_types']:
                user['sub_types'].append('5')
                await message.answer("Ты подписан на уведомления треговги по ритму")
            else:
                user['sub_types'].remove('5')
                await message.answer("Ты отписан от уведомлений треговги по ритму")
            with open('users.json', 'w') as file:
                json.dump(users, file)


@dp.message_handler(commands=['unsubscribe'])
async def unsubscribe(message: types.Message):
    users = get_users()
    for user in users:
        if user['user_id'] == message.chat.id:
            user['sub_types'] = []
            with open('users.json', 'w') as file:
                json.dump(users, file)
            await message.answer("Ты отписан от всех уведомлений ❎")


@dp.message_handler(commands=['настройки'])
async def settings(message: types.Message):
    await message.answer(
        "Ты можешь подписаться на уведомления о критических тревогах, сигнал тревоги или для привлечения внимания нажми /1, /2, /3, /4, /5",
        reply_markup=kb.sub_list_menu())


@dp.message_handler(commands=['nurjunud'])
async def nurjunud(message: types.Message):
    await message.answer(get_failed_cows())
    await message.delete()


@dp.message_handler()
async def echo(message: types.Message):
    await message.answer(message.text)


if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    loop.create_task(get_new_errors())
    asyncio.set_event_loop(loop)
    executor.start_polling(dp, skip_updates=True)
