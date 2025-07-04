from telebot import TeleBot
import requests
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



def geolocator(lat, lon, language='ru'):
    key = '628f2653605142aab396a036e804cc96'
    url = f'https://api.opencagedata.com/geocode/v1/json?q={lat}+{lon}&key={key}&language={language}&pretty=1'
    response = requests.get(url)
    data = response.json()
    return data['results'][0]['formatted'] if data['results'] else None



print("Конфигурация загружена успешно")