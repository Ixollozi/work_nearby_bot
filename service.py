from math import radians, cos, sin, asin, sqrt
from database import get_db
from models import *
from all_txt import *
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

def get_user(user_id):
    # noinspection PyTypeChecker
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

def update_user_role(user_id: int, new_role: str):
    user = db.query(User).filter(User.tg_id == user_id).first()
    if user:
        user.role = new_role
        db.commit()

# --- Категории ---
def get_category_id(category_name):
    category = db.query(Category).filter(Category.name == category_name).first()
    return category.id if category else None

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
    return distance_km * 1000


def get_vacancies_nearby(user_lat, user_lon, radius_meters, categories=None):
    all_vacancies = db.query(Vacancy).filter(Vacancy.expires_at >= datetime.utcnow()).all()
    filtered = []
    if not categories:
        return []

    for v in all_vacancies:
        if v.category not in categories:
            continue
        # Если выбран "Все вакансии", игнорируем радиус
        if radius_meters == lang['all_vacancies']['ru']:  # Проверяем по русскому варианту
            filtered.append((v, 0))  # Добавляем без учета расстояния
        else:
            # Рассчитываем расстояние
            distance = calculate_distance(user_lat, user_lon, v.latitude, v.longitude)
            radius_value = int(radius_meters.replace('m', '')) if isinstance(radius_meters, str) else radius_meters
            if distance <= radius_value:
                filtered.append((v, distance))

    # Сортируем по расстоянию (если радиус учитывается)
    return sorted(filtered, key=lambda x: x[1])


def get_vacancy_by_id(vacancy_id):
    return db.query(Vacancy).filter(Vacancy.id == vacancy_id).first()

def get_vacancy_by_title(title):
    return db.query(Vacancy).filter(Vacancy.title == title).first()

def delete_vacancy(vacancy_name, user_id):
    vacancy = db.query(Vacancy).filter(Vacancy.title == vacancy_name, Vacancy.user_id == user_id).first()
    if vacancy:
        db.delete(vacancy)
        db.commit()
        return True
    return False




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