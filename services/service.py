from math import radians, cos, sin, asin, sqrt
from database.base import *
from configuration.lang_loader import *
from geopy.geocoders import Nominatim
from sqlalchemy.orm import Session
from datetime import datetime
from deep_translator import GoogleTranslator
from difflib import get_close_matches


db: Session = next(get_db())

def initialize_categories():
    CATEGORIES = ['Разработка и IT', 'Дизайн', 'Маркетинг', 'Продажи', 'Сопровождение', 'Другое']
    existing_category_names = [c.name for c in get_all_categories()]
    for category_name in CATEGORIES:
        if category_name not in existing_category_names:
            create_category(category_name)
    print("Категории успешно инициализированы")

# --- Пользователи ---
def create_user(tg_id, username, name, phone, language, latitude, longitude, role, prefered_radius):
    user = User(
        tg_id=tg_id,
        username=username,
        name=name,
        phone=phone,
        language=language,
        latitude=latitude,
        longitude=longitude,
        role=role,
        prefered_radius=prefered_radius
    )
    db.add(user)
    db.commit()

def get_user(user_id):
    user = db.query(User).filter(User.tg_id == user_id).first()
    return user

def get_user_by_phone(phone):
    return db.query(User).filter(User.phone == phone).first()


def get_all_users():
    return db.query(User).all()


def get_users_paginated(page=1, page_size=10):
    offset = (page - 1) * page_size
    return db.query(User).offset(offset).limit(page_size).all()


def count_users():
    return db.query(User).count()


def get_admin(tg_id):
    return db.query(User).filter(User.tg_id == tg_id, User.is_admin == True).first()

def get_all_admins():
    name = db.query(User.name).filter(User.is_admin == True).all()
    return name

def update_user_field(user_id, **kwargs):
    user = db.query(User).filter(User.tg_id == user_id).first()
    if user:
        for key, value in kwargs.items():
            setattr(user, key, value)
        db.commit()

# --- Категории ---
def get_category_id(category_name):
    category = db.query(Category).filter(Category.name == category_name).first()
    return category.id if category else None

def get_all_categories():
    """Получить все категории"""
    return db.query(Category).all()

def get_category_by_id(category_id):
    return db.query(Category).filter(Category.id == category_id).first()

def create_category(name):
    category = Category(name=name)
    db.add(category)
    db.commit()

def delete_category(category_name):
    category = db.query(Category).filter(Category.name == category_name).first()
    db.delete(category)
    db.commit()


def add_user_category(user_id, category_id):
    category = db.query(Category).filter(Category.id == category_id).first()
    user = db.query(User).filter(User.tg_id == user_id).first()

    if category not in user.categories:
        user.categories.append(category)
        db.commit()


def get_user_categories(user_id):
    try:
        user = db.query(User).filter(User.tg_id == user_id).first()
        if not user:
            return []
        categories = user.categories or []
        return categories
    except Exception as e:
        print(f"[ERROR get_user_categories] {e}")
        return []



def delete_user_category(user_id, category_id):
    category = db.query(Category).filter(Category.id == category_id).first()
    user = db.query(User).filter(User.tg_id == user_id).first()
    user.categories.remove(category)
    db.commit()


# --- Вакансии ---
def create_vacancy(user_id, title, description, payment, latitude, longitude, contact, category, expires_at, priority=False):
    vacancy = Vacancy(
        user_id=user_id,
        title=title,
        description=description,
        payment=payment,
        latitude=latitude,
        longitude=longitude,
        contact=contact,
        category=category,
        expires_at=expires_at,
        priority=priority
    )
    db.add(vacancy)
    db.commit()

def get_user_vacancies(user_id):
    return db.query(Vacancy).filter(Vacancy.user_id == user_id).all()

def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371.0
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * asin(sqrt(a))
    distance_km = R * c
    return distance_km
def get_vacancies_nearby(user_lat, user_lon, radius_meters, categories=None):
    all_vacancies = db.query(Vacancy).filter(Vacancy.expires_at >= datetime.utcnow()).all()
    filtered = []

    if not categories:
        return []

    # Обрабатываем случай "все вакансии"
    if str(radius_meters) in ['📄 All vacancies', lang['all_vacancies']['ru'], 'all']:
        for v in all_vacancies:
            if v.category in categories:
                filtered.append((v, 0))
        return filtered

    # Проверяем координаты пользователя
    if user_lat is None or user_lon is None:
        for v in all_vacancies:
            if v.category in categories:
                filtered.append((v, 0))
        return filtered

    # Парсим радиус
    try:
        if isinstance(radius_meters, str):
            radius_value = int(radius_meters.replace('m', ''))
        else:
            radius_value = int(radius_meters)
    except (ValueError, TypeError):
        print(f"[ERROR] Неверный формат радиуса: {radius_meters}")
        return []

    # Фильтруем по категории и расстоянию
    for v in all_vacancies:
        if v.category not in categories:
            continue

        try:
            distance = calculate_distance(user_lat, user_lon, v.latitude, v.longitude)
            if distance <= radius_value:
                filtered.append((v, distance))
        except Exception as e:
            print(f"[ERROR] Не удалось рассчитать расстояние для вакансии ID={v.id}: {e}")
            continue

    # Сортировка по расстоянию
    filtered.sort(key=lambda x: x[1])

    return filtered

def get_all_vacancies():
    return db.query(Vacancy).filter(Vacancy.expires_at >= datetime.utcnow()).all()

def get_vacancy_by_id(vacancy_id):
    return db.query(Vacancy).filter(Vacancy.id == vacancy_id).first()

def get_vacancy_by_title(title):
    return db.query(Vacancy).filter(Vacancy.title == title).first()

def get_address_from_coordinates(latitude, longitude):
    geolocator = Nominatim(user_agent="vacancy_bot")
    location = geolocator.reverse((latitude,longitude))
    return location



def match_category_from_user_input(user_input, user_language):
    categories = get_all_categories()
    user_input_lower = user_input.lower()

    # Сначала проверка по переводу всех категорий в язык пользователя
    for category in categories:
        try:
            translated = GoogleTranslator(source='auto', target=user_language).translate(category.name).lower()
            if translated == user_input_lower:
                return category.name  # Возвращаем имя на русском
        except Exception as e:
            print(f"[ERROR translate compare] {e}")

    # Проверка напрямую, вдруг пользователь ввел русскую категорию
    for category in categories:
        if category.name.lower() == user_input_lower:
            return category.name

    # Если не найдено
    return None


    # 3. Поиск похожих значений
    match = get_close_matches(user_input, all_names_lower, n=1, cutoff=0.75)
    if match:
        return all_names[all_names_lower.index(match[0])]

    return None

def delete_vacancy(vacancy_id, user_id):
    try:
        vacancy = db.query(Vacancy).filter(Vacancy.id == vacancy_id).first()
        if not vacancy:
            return False

        if vacancy.user_id != user_id:
            return False

        db.delete(vacancy)
        db.commit()
        return True
    except Exception as e:
        print(f"Error deleting vacancy: {e}")
        db.rollback()
        return False


def delete_vacancy_by_admin(vacancy_id):
    try:
        # Сначала удаляем связанные записи
        db.query(Response).filter(Response.vacancy_id == vacancy_id).delete()
        db.query(Favorite).filter(Favorite.vacancy_id == vacancy_id).delete()

        # Затем удаляем саму вакансию
        vacancy = db.query(Vacancy).filter(Vacancy.id == vacancy_id).first()
        if vacancy:
            db.delete(vacancy)
            db.commit()
            return True
        return False
    except Exception as e:
        print(f"Error deleting vacancy: {e}")
        db.rollback()
        return False




# --- Отклики ---
def respond_to_vacancy(user_id, vacancy_id):
    response = Response(user_id=user_id, vacancy_id=vacancy_id)
    db.add(response)
    db.commit()

def get_user_responses(user_id):
    return db.query(Response).filter(Response.user_id == user_id).all()

def get_vacancy_responses_count(vacancy_id):
    return db.query(Response).filter(Response.vacancy_id == vacancy_id).count()

def has_user_responded(user_id, vacancy_id):
    return db.query(Response).filter(Response.user_id == user_id, Response.vacancy_id == vacancy_id).first() is not None


# --- Избранное ---
def add_to_favorites(user_id, vacancy_id):
    fav = Favorite(user_id=user_id, vacancy_id=vacancy_id)
    db.add(fav)
    db.commit()



def get_favorites(user_id):
    a = db.query(Favorite).filter(Favorite.user_id == user_id).all()
    return a

def delete_user_favorite(user_id, vacancy_id):
    favorite = db.query(Favorite).filter(Favorite.user_id == user_id, Favorite.vacancy_id == vacancy_id).first()
    if favorite:
        db.delete(favorite)
        db.commit()
        return True
    return False

def is_favorite(user_id, vacancy_id):
    return db.query(Favorite).filter(Favorite.user_id == user_id, Favorite.vacancy_id == vacancy_id).first() is not None

# --- Удаление ---
def delete_expired_vacancies():
    expired = db.query(Vacancy).filter(Vacancy.expires_at < datetime.utcnow()).all()
    for v in expired:
        db.delete(v)
    db.commit()

def delete_expired_responses():
    expired = db.query(Response).filter(Response.expires_at < datetime.utcnow()).all()
    for v in expired:
        db.delete(v)
    db.commit()


# --- admin ---

def add_admin(tg_id):
    user = db.query(User).filter(User.tg_id == tg_id).first()
    if user:
        user.is_admin = 1
        db.commit()

def remove_admin(tg_id):
    user = db.query(User).filter(User.tg_id == tg_id).first()
    if user:
        user.is_admin = 0
        db.commit()

