from telebot import types
from all_txt import lang
from service import *
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton


def get_language():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton('Uzbek', callback_data='uz'),
               InlineKeyboardButton('Русский', callback_data='ru'))
    return markup

def get_phone(language):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    phone = KeyboardButton(lang['phone'][language], request_contact=True)
    kb.add(phone)
    return kb


def get_role_keyboard(language):
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    if language == 'uz':
        markup.add(KeyboardButton("👨‍🔧 Аrizachi"), KeyboardButton("🏢 Ish beruvchi"))
    else:
        markup.add(KeyboardButton("👨‍🔧 Соискатель"), KeyboardButton("🏢 Работодатель"))
    return markup

def get_radius(language):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    radius = KeyboardButton('1000m')
    radius1 = KeyboardButton('5000m')
    radius2 = KeyboardButton('10000m')
    all_vacancy = KeyboardButton(lang['all_vacancies'][language])

    kb.add(radius, radius1, radius2, all_vacancy)
    return kb

def get_role(language):
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    if language == "ru":
        markup.add(KeyboardButton("Искатель"),
                KeyboardButton("Работодатель"))
    else:
        markup.add(KeyboardButton("Ish izlovchi", ),
                   KeyboardButton("Ish beruvchi",))
    return markup

def main_menu(tg_id,language):
    markup = InlineKeyboardMarkup(row_width=2)
    user = get_user(tg_id)
    if user.role == 'искатель':
        find_job = InlineKeyboardButton(lang['main_menu']['find_job'][language], callback_data='find_job')
        favorite = InlineKeyboardButton(lang['main_menu']['favorite'][language], callback_data='favorite')
        settings = InlineKeyboardButton(lang['main_menu']['settings'][language], callback_data='settings')
        markup.add(find_job,favorite, settings)
    elif user.role == 'работодатель':
        find_job = InlineKeyboardButton(lang['main_menu']['create_job'][language], callback_data='create_job')
        favorite = InlineKeyboardButton(lang['main_menu']['favorite'][language], callback_data='favorite')
        settings = InlineKeyboardButton(lang['main_menu']['settings'][language], callback_data='settings')
        markup.add(find_job,favorite, settings)
    return markup

def admin_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add('⭐️ Все админы ⭐️','🗂 Все категории 🗂' ,
               '⭐️ Добавить админа', '🗂 Добавить категорию',
               '⭐️ Удалить админа','🗂 Удалить категорию',
               '📋 Список пользователей', '❌ Выход из админки')
    return markup

def cancel():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add('❌ Отменить')
    return markup

def get_currency_keyboard():
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("UZS", callback_data="currency_UZS"),
        InlineKeyboardButton("USD", callback_data="currency_USD"),
        InlineKeyboardButton("RUB", callback_data="currency_RUB")
    )
    return markup


def get_categories_keyboard(language):
    markup = InlineKeyboardMarkup()
    categories = get_all_categories()
    for category in categories:
        markup.row(InlineKeyboardButton(category.name, callback_data=f"category_{category.name}"))
    return markup