from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def sub_list_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton('/1'))
    markup.insert(KeyboardButton('/2'))
    markup.insert(KeyboardButton('/3'))
    markup.insert(KeyboardButton('/4'))
    markup.insert(KeyboardButton('/5'))
    markup.insert(KeyboardButton('/unsubscribe'))
    markup.insert(KeyboardButton('/exit'))
    return markup



def main_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton('/nurjunud'))
    markup.insert(KeyboardButton('/настройки'))
    return markup
