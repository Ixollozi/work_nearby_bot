from telebot import types
from services.service import *
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from deep_translator import GoogleTranslator
from configuration.config import (user_vacancy_index, user_vacancies_list, user_favorites_list,
                                  user_favorite_index, user_responses_list, user_response_index)



def get_language():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton('Uzbek', callback_data='uz'),
               InlineKeyboardButton('Русский', callback_data='ru'),
               InlineKeyboardButton('English', callback_data='en'))
    return markup

def change_language():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton('Uzbek', callback_data='change_uz'),
               InlineKeyboardButton('Русский', callback_data='change_ru'),
               InlineKeyboardButton('English', callback_data='change_en'))
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
    elif language == 'en':
        markup.add(KeyboardButton("👨‍🔧 Seeker"), KeyboardButton("🏢 Employer"))
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
    if user.role == '👨‍🔧 соискатель' or user.role == '👨‍🔧 arizachi' or user.role == '👨‍🔧 seeker':
        find_job = InlineKeyboardButton(lang['main_menu']['find_job'][language], callback_data='find_job')
        category = InlineKeyboardButton(lang['main_menu']['category'][language], callback_data='category')
        my_response = InlineKeyboardButton(lang['main_menu']['my_response'][language], callback_data='my_response')
        favorite = InlineKeyboardButton(lang['main_menu']['favorite'][language], callback_data='favorite')
        settings = InlineKeyboardButton(lang['main_menu']['settings'][language], callback_data='settings')
        markup.row(find_job,category, my_response)
        markup.add(favorite, settings)
    elif user.role == '🏢 работодатель' or user.role == '🏢 ish beruvchi' or user.role == '🏢 employer':
        find_job = InlineKeyboardButton(lang['main_menu']['create_job'][language], callback_data='create_job')
        my_vacancy = InlineKeyboardButton(lang['main_menu']['my_jobs'][language], callback_data='my_vacancy')
        user_response = InlineKeyboardButton(lang['main_menu']['user_responses'][language], callback_data='user_responses')
        settings = InlineKeyboardButton(lang['main_menu']['settings'][language], callback_data='settings')
        markup.add(find_job,my_vacancy,user_response, settings)
    return markup

def admin_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add('📋 Список пользователей')
    markup.add('⭐️ Добавить админа','⭐️ Удалить админа')
    markup.add('⭐️ Все админы ⭐️')
    markup.add( '🗂 Добавить категорию','🗂 Удалить категорию')
    markup.add('🗂 Все категории 🗂')
    markup.add('⚙️ Настройки', '🔍 Найти и удалить вакансию')
    markup.add('❌ Выход из админки')
    return markup

def cancel():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add('❌ Отменить')
    return markup

def agree(language):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    if language == 'uz':
        markup.add('❌ Bekor qilish','✅ Qabul qilish')
    elif language == 'en':
        markup.add('❌ Cancel','✅ Agree')
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
    markup.add(KeyboardButton('❌ Отменить'))
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


def get_vacancy_keyboard(language):
    markup = InlineKeyboardMarkup(row_width=2)
    next_vacancy = InlineKeyboardButton(lang['get_vacancy_kb'][language][0], callback_data="next_vacancy")
    favorite = InlineKeyboardButton(lang['get_vacancy_kb'][language][1], callback_data="add_to_favorite")
    respond = InlineKeyboardButton(lang['get_vacancy_kb'][language][2], callback_data="respond")
    main_menu = InlineKeyboardButton(lang['get_vacancy_kb'][language][3], callback_data="main_menu")
    markup.add(next_vacancy, favorite, respond, main_menu)
    return markup



def navigation(user_id,item_type='response'):
    nav = InlineKeyboardMarkup()
    if item_type == 'response':
        response_id = user_responses_list[user_id][user_response_index[user_id]].id
        nav.add(
            InlineKeyboardButton("⬅️", callback_data="response_prev"),
            InlineKeyboardButton("❌", callback_data=f"response_delete_{response_id}"),
            InlineKeyboardButton("➡️", callback_data="response_next")
        )
        nav.row(InlineKeyboardButton("🏠", callback_data="main_menu"))
    elif item_type == 'vacancy':
        vacancy_id = user_vacancies_list[user_id][user_vacancy_index[user_id]].id
        nav.add(
            InlineKeyboardButton("⬅️", callback_data="job_prev"),
            InlineKeyboardButton("❌", callback_data=f"job_delete_{vacancy_id}"),
            InlineKeyboardButton("➡️", callback_data="job_next")
        )
        nav.row(InlineKeyboardButton("🏠", callback_data="main_menu"))
    elif item_type == 'favorite':
        favorite_id = user_favorites_list[user_id][user_favorite_index[user_id]].id
        nav.add(InlineKeyboardButton("⬅️", callback_data='favorite_prev'),
                InlineKeyboardButton(f"❌ ", callback_data=f'favorite_delete_{favorite_id}'),
                InlineKeyboardButton("➡️", callback_data='favorite_next'))
        nav.row(InlineKeyboardButton("🏠", callback_data="main_menu"))
    return nav


def settings_kb(language):
    markup = InlineKeyboardMarkup(row_width=2)
    edit_profile = InlineKeyboardButton(lang['settings'][language][0], callback_data="edit_profile")
    change_language = InlineKeyboardButton(lang['settings'][language][1], callback_data="change_language")
    change_radius = InlineKeyboardButton(lang['settings'][language][2], callback_data="change_radius")
    switch_role = InlineKeyboardButton(lang['settings'][language][3], callback_data="switch_role")
    back = InlineKeyboardButton(lang['settings'][language][4], callback_data="main_menu")
    markup.add(edit_profile, change_language, change_radius, switch_role, back)
    return markup


