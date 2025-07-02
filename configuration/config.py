from telebot import TeleBot
from geopy.geocoders import Nominatim
from services.service import *
import logging
from dotenv import load_dotenv
import os

# Настройка логирования для отладки
logging.basicConfig(level=logging.INFO)

load_dotenv()
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")


# Глобальные переменные и константы
bot = TeleBot(BOT_TOKEN)
ADMINS = [385688612]
CATEGORIES = ['Разработка и IT', 'Дизайн', 'Маркетинг', 'Продажи', 'Сопровождение', 'Другое']

# Словари для хранения состояний
chat_pages = {}
user_create_job_data = {}
user_vacancy_index = {}
user_vacancies_list = {}
user_responses_list = {}
user_response_index = {}

# Геолокатор
geolocator = Nominatim(user_agent="Ishbor_telegram_bot")

# Инициализация категорий
try:
    existing_category_names = [c.name for c in get_all_categories()]
    for i in CATEGORIES:
        if i not in existing_category_names:
            create_category(i)
    print("Категории успешно инициализированы")
except Exception as e:
    print(f"Ошибка при инициализации категорий: {e}")

delete_expired_vacancies()
delete_expired_responses()


print("Конфигурация загружена успешно")