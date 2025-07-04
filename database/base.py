from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, String, Float, ForeignKey, Boolean, DateTime, Text, Table
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, 'bot_base.db')

engine = create_engine(f'sqlite:///{db_path}')

Session = sessionmaker(bind=engine)

Base = declarative_base()

def get_db():
    db = Session()
    try:
        yield db
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()




# Промежуточная таблица для связи "многие ко многим" между User и Category
user_categories = Table(
    'user_categories',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('category_id', Integer, ForeignKey('categories.id'))
)

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    tg_id = Column(Integer, nullable=False, unique=True)
    username = Column(String)
    name = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    language = Column(String, nullable=False)
    latitude = Column(Float )
    longitude = Column(Float)
    prefered_radius = Column(Integer)
    role = Column(String, nullable=False)  # соискатель / работодатель
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Связи
    vacancies = relationship("Vacancy", back_populates="owner")
    favorites = relationship("Favorite", back_populates="user")
    categories = relationship("Category", secondary=user_categories, back_populates="users")

class Category(Base):
    __tablename__ = 'categories'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)

    # Назад к пользователям
    users = relationship("User", secondary=user_categories, back_populates="categories")
    vacancies = relationship("Vacancy", back_populates="category_fk")

class Vacancy(Base):
    __tablename__ = 'vacancies'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    payment = Column(String, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    contact = Column(String, nullable=False)
    category = Column(Integer, ForeignKey('categories.id'))
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, default=lambda: datetime.utcnow() + timedelta(days=7))
    priority = Column(Boolean, default=False)

    owner = relationship("User", back_populates="vacancies")
    responses = relationship("Response", back_populates="vacancy")
    category_fk = relationship("Category", back_populates="vacancies")

class Favorite(Base):
    __tablename__ = 'favorites'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    vacancy_id = Column(Integer, ForeignKey('vacancies.id'))

    user = relationship("User", back_populates="favorites")
    vacancy = relationship("Vacancy")

class Response(Base):
    __tablename__ = 'responses'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.tg_id'))
    vacancy_id = Column(Integer, ForeignKey('vacancies.id'))
    response_time = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, default=lambda: datetime.utcnow() + timedelta(days=30))

    vacancy = relationship("Vacancy", back_populates="responses")

# Favorite.__table__.drop(bind=engine)
Base.metadata.create_all(bind=engine)


