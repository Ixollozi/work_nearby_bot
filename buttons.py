from telebot import types
from all_txt import lang
from service import *
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from deep_translator import GoogleTranslator



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


def main_menu(tg_id,language):
    markup = InlineKeyboardMarkup(row_width=2)
    user = get_user(tg_id)
    if user.role == '👨‍🔧 соискатель' or user.role == '👨‍🔧 arizachi':
        find_job = InlineKeyboardButton(lang['main_menu']['find_job'][language], callback_data='find_job')
        category = InlineKeyboardButton(lang['main_menu']['category'][language], callback_data='category')
        favorite = InlineKeyboardButton(lang['main_menu']['favorite'][language], callback_data='favorite')
        settings = InlineKeyboardButton(lang['main_menu']['settings'][language], callback_data='settings')
        markup.add(find_job,category, favorite, settings)
    elif user.role == '🏢 работодатель' or user.role == '🏢 ish beruvchi':
        find_job = InlineKeyboardButton(lang['main_menu']['create_job'][language], callback_data='create_job')
        my_vacancy = InlineKeyboardButton(lang['main_menu']['my_jobs'][language], callback_data='my_vacancy')
        settings = InlineKeyboardButton(lang['main_menu']['settings'][language], callback_data='settings')
        markup.add(find_job,my_vacancy, settings)
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

def agree(language):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    if language == 'uz':
        markup.add('❌ Отменить','✅ Qabul qilish')
    else:
        markup.add('❌ Отменить','✅ Подтвердить')
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

def category_keyboard(language):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    categories = get_all_categories()

    lang_code = {
        'ru': 'ru',
        'uz': 'uz',
        'en': 'en'
    }.get(language, 'ru')
    for category in categories:
        try:
            translated = GoogleTranslator(source='auto', target=lang_code).translate(category.name)
        except Exception as e:
            print(f"[ERROR translate_category] {e}")
            translated = category.name
        markup.add(KeyboardButton(translated))

    return markup

def create_or_delete(language, mode):
    markup = InlineKeyboardMarkup()

    if mode == 'category':
        create_cb = 'create'
        delete_cb = 'delete'
    elif mode == 'vacancy':
        create_cb = 'vacancy_create'
        delete_cb = 'vacancy_delete'
    elif mode == 'favorite':
        create_cb = 'favorite_create'
        delete_cb = 'favorite_delete'
    else:
        create_cb = 'create'
        delete_cb = 'delete'

    markup.add(
        InlineKeyboardButton(lang['create_or_delete'][language][1], callback_data=delete_cb),
        InlineKeyboardButton(lang['create_or_delete'][language][0], callback_data=create_cb)
    )
    markup.row(InlineKeyboardButton(lang['create_or_delete'][language][2], callback_data='main_menu'))
    return markup


def vacancy_keyboard(tg_id,language):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    vacancies = get_user_vacancies(tg_id)
    for vacancy in vacancies:
        try:
            translated = GoogleTranslator(source='auto', target=language).translate(vacancy.title)
        except Exception as e:
            print(f"[ERROR translate_vacancy] {e}")
            translated = vacancy.name
        markup.add(KeyboardButton(translated))
    return markup

def delete_vacancy_keyboard(tg_id):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    vacancies = get_user_vacancies(tg_id)
    for vacancy in vacancies:
        markup.add(KeyboardButton(vacancy.title))

    markup.row('❌ Отменить')
    return markup

