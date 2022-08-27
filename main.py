import asyncio
import datetime
import json
import logging
import bs4
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils import executor

import config

API_TOKEN = config.auth_token  # Токен бота

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)


def get_errors_from_server(errortype=1, deviceaddr='', errorcode='', page=1 , datefrom=datetime.date.today()) -> list:
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
              '2': deviceaddr,
              'Multisort': '2:1:1|',
              '4': datefrom,  # date max 11 day before
              '5': errortype,
              '8': '1,0,1'}

    headers = {'Content-Type': 'application/json'}

    url = config.server + '/T4C/Content/AjaxRequest.aspx'
    response = session.get(url, headers=headers, params=params)
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
            print(new_error)
            if new_error in errors:
                continue
            else:
                errors.append(new_error)
                new_errors.append(new_error)
    with open('errors.json', 'w') as file:
        json.dump(errors, file)

    return new_errors


def login():
    """Login to .net server T4C"""
    values = dict(txtUserName=config.username,
                  txtPassword=config.password,
                  btnLogin_5='Login',
                  __EVENTARGUMENT='',
                  __EVENTTARGET=''
                  )
    with requests.Session() as s:
        response = s.post(config.server + "/T4C/Content/Login.aspx", data=values)
        logging.info(response.status_code)
    return s


@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.Message):
    await message.reply("Hi!\nI'm T4CBot!\nPowered by aiogram.", reply_markup=keyboard)
    await message.delete()


async def get_new_errors():
    while True:

        new_errors = get_errors_from_server()
        print(len(new_errors))
        if new_errors:
            """send first 10 errors"""
            message = ''
            for error in new_errors[:10]:
                message += f"{error['date']}\n{error['device_address']} {error['description']}\n"
            await bot.send_message(config.user_id, message, disable_notification=True)
        await asyncio.sleep(10)


if __name__ == '__main__':
    session = login()
    loop = asyncio.new_event_loop()
    loop.create_task(get_new_errors())
    asyncio.set_event_loop(loop)
    executor.start_polling(dp, skip_updates=True)
