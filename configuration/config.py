from telebot import TeleBot
from geopy.geocoders import Nominatim
from services.service import *
import logging

# Настройка логирования для отладки
logging.basicConfig(level=logging.INFO)

# Глобальные переменные и константы
bot = TeleBot('7981973749:AAE_3acJdzQTfCMsuH9zi46oXtwS_w6Gj5Q')
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
# update_user_field(385688612, role='👨‍🔧 соискатель')
update_user_field(385688612, role='🏢 работодатель')
update_user_field(385688612, prefered_radius=None)

print("Конфигурация загружена успешно")