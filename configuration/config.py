from telebot import TeleBot
from services.service import get_cost, create_cost
import requests
import logging
from dotenv import load_dotenv
import os

# Настройка логирования для отладки
logging.basicConfig(level=logging.INFO)

load_dotenv()
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CLICK_MERCHANT_ID = os.getenv('CLICK_MERCHANT_ID')
CLICK_SECRET_KEY = os.getenv('CLICK_SECRET_KEY')
PAYMENT_PROVIDER_TOKEN = os.getenv('PAYMENT_PROVIDER_TOKEN')

create_cost()
cost = get_cost()
PAYMENT_AMOUNT = cost * 100


# Глобальные переменные и константы
bot = TeleBot(BOT_TOKEN)
ADMINS = [385688612, 1868376]
CATEGORIES = ['Разработка и IT', 'Дизайн', 'Маркетинг', 'Продажи', 'Сопровождение', 'Другое']

# Словари для хранения состояний
user_state = {}
chat_pages = {}
user_create_job_data = {}
user_vacancy_index = {}
user_vacancies_list = {}
user_responses_list = {}
user_response_index = {}
user_favorites_list = {}
user_favorite_index = {}
user_payment = {}

# Геолокатор



def geolocator(lat, lon, language='ru'):
    key = '628f2653605142aab396a036e804cc96'
    url = f'https://api.opencagedata.com/geocode/v1/json?q={lat}+{lon}&key={key}&language={language}&pretty=1'
    response = requests.get(url)
    data = response.json()
    return data['results'][0]['formatted'] if data['results'] else None



print("Конфигурация загружена успешно")