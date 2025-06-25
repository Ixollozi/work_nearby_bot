from math import radians, cos, sin, asin, sqrt
from database import get_db
from models import *

from sqlalchemy.orm import Session
from datetime import datetime

db: Session = next(get_db())

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


def get_user(tg_id):
    return db.query(User).filter(User.tg_id == tg_id).first()


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


# --- Категории ---

def get_all_categories():
    name = db.query(Category.name).all()
    return name

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


def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Вычисляет расстояние между двумя координатами в метрах.
    """
    # Радиус Земли в километрах
    R = 6371.0

    # Конвертация координат в радианы
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * asin(sqrt(a))

    distance_km = R * c
    return distance_km * 1000  # перевод в метры

def get_vacancies_nearby(user_lat, user_lon, radius_meters, category=None):# функция для расчёта расстояния
    all_vacancies = db.query(Vacancy).filter(Vacancy.expires_at >= datetime.utcnow()).all()
    filtered = []
    for v in all_vacancies:
        if category and v.category.lower() != category.lower():
            continue
        distance = calculate_distance(user_lat, user_lon, v.latitude, v.longitude)
        if distance <= radius_meters:
            filtered.append((v, distance))
    return sorted(filtered, key=lambda x: x[1])


def get_vacancy_by_id(vacancy_id):
    return db.query(Vacancy).filter(Vacancy.id == vacancy_id).first()

# --- Отклики ---
def respond_to_vacancy(user_id, vacancy_id):
    response = Response(user_id=user_id, vacancy_id=vacancy_id)
    db.add(response)
    db.commit()

# --- Избранное ---
def add_to_favorites(user_id, vacancy_id):
    fav = Favorite(user_id=user_id, vacancy_id=vacancy_id)
    db.add(fav)
    db.commit()


def get_favorites(user_id):
    return db.query(Favorite).filter(Favorite.user_id == user_id).all()


def is_favorite(user_id, vacancy_id):
    return db.query(Favorite).filter(Favorite.user_id == user_id, Favorite.vacancy_id == vacancy_id).first() is not None

# --- Удаление ---
def delete_expired_vacancies():
    expired = db.query(Vacancy).filter(Vacancy.expires_at < datetime.utcnow()).all()
    for v in expired:
        db.delete(v)
    db.commit()