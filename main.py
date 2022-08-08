import pandas as pd
import bs4
import requests
import lxml
import logging

from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
import config

API_TOKEN = config.auth_token

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
keyboard.add(KeyboardButton(text='🚨🚨🚨'))
keyboard.insert(KeyboardButton(text='🚨'))
keyboard.insert(KeyboardButton(text='⚠️'))
keyboard.insert(KeyboardButton(text='ℹ️'))


def get_errors(errortype='', deviceaddr=''):
    """Логин на сервер за табличкой с ошибками

    :param deviceaddr:
    :param errortype: тип ошибки в базе сервера T4C. 1-5 "1" > Критическая тревога <
    "2" > Сигнал тревоги <
    "3" > Сигнал для привлечения внимания <
    "4" > Доклад <
    "5" > Сигнал тревоги по ритму <
    """

    values = {'txtUserName': config.username,
              'txtPassword': config.password,
              'btnLogin_5': 'Login',
              '__EVENTARGUMENT': '',
              '__EVENTTARGET': ''}
    with requests.Session() as session:
        session.post(config.server + '/T4C/Content/Login.aspx', data=values)
        url = config.server + '/T4C/Content/AjaxRequest.aspx?Module=53&PageNo=1&MaxParams=9&0=2&1=1&2=' \
              + deviceaddr + '&MultiSort=2:1:1|&6=&5=' + errortype + '&7=&8=1,0,1'
        headers = {'Content-type': 'application/json'}
        response = session.post(url, headers=headers, json={'autoRefresh': 'true'})
        table = bs4.BeautifulSoup(response.content, features="lxml")

    errorslist = ''
    for tr in table.findAll('tr', limit=5):
        td = tr.findAll('td')
        # print(td[0].text)
        errorslist += str(td[0].text + ' ' + td[5].text + ' ' + td[2].text + '\n')
    return errorslist


@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.Message):
    await message.reply("Hi!\nI'm T4CBot!\nPowered by aiogram.", reply_markup=keyboard)
    await message.delete()


@dp.message_handler(text='🚨🚨🚨', user_id=config.user_id)
async def send_welcome(message: types.Message):
    await message.reply(get_errors('1'), reply_markup=keyboard)
    await message.delete()


@dp.message_handler(text='🚨', user_id=config.user_id)
async def send_welcome(message: types.Message):
    await message.reply(get_errors('2'), reply_markup=keyboard)
    await message.delete()


@dp.message_handler(text='⚠️', user_id=config.user_id)
async def send_welcome(message: types.Message):
    await message.reply(get_errors('3'), reply_markup=keyboard)
    await message.delete()


@dp.message_handler(text='ℹ️', user_id=config.user_id)
async def send_welcome(message: types.Message):
    await message.reply(get_errors('4'), reply_markup=keyboard)
    await message.delete()


@dp.message_handler(user_id=config.user_id)
async def send_welcome(message: types.Message):
    await message.reply(get_errors(), reply_markup=keyboard)
    await message.delete()


def main():
    executor.start_polling(dp, skip_updates=True)


if __name__ == '__main__':
    main()
