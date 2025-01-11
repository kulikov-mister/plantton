# db/models.py
import os
from sqlalchemy import create_engine, Column, Integer, String, Boolean, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship, declarative_base, sessionmaker
from datetime import datetime


base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Инициализация базы данных SQLite
DATABASE_URL = f'sqlite:///{base_dir}/bot_database.db'
print(DATABASE_URL)
engine = create_engine(DATABASE_URL, echo=False)
Base = declarative_base()
SessionLocal = sessionmaker(bind=engine)


# 1. Модель пользователей
class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, unique=True, nullable=False)  # Telegram user ID
    pro = Column(Boolean, default=False)  # Статус подписки
    charge_id = Column(String, unique=True, nullable=False)
    balance = Column(Integer, default=0)  # Баланс во внутренней валюте
    subscribed = Column(Boolean, default=False)  # Статус подписки на новости
    date = Column(DateTime, default=datetime.now())

    # Связь с платежами и книгами
    payments = relationship('Payment', back_populates='user')
    books = relationship('Book', back_populates='user')
    orders = relationship('Order', back_populates='user')


# 2. Модель платежей
class Payment(Base):
    __tablename__ = 'payments'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))  # ID пользователя
    amount = Column(Integer, nullable=False)  # Сумма пополнения
    charge_id = Column(String, nullable=False)  # Id операции
    date = Column(DateTime, default=datetime.now())
    refunded = Column(Boolean, default=False)  # Статус возврата транзакции

    # Связь с пользователем
    user = relationship('User', back_populates='payments')


# 3. Модель заказов
class Order(Base):
    __tablename__ = 'orders'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))  # ID пользователя
    book_id = Column(Integer, ForeignKey('books.id'))  # ID книги
    amount = Column(Integer, default=0)  # Сумма списания во внутренней валюте
    book_url = Column(String, nullable=False)  # Ссылка на книгу
    date = Column(DateTime, default=datetime.now())

    # Связи с пользователем и книгой
    user = relationship('User', back_populates='orders')
    book = relationship('Book', back_populates='orders')


# 4. Модель категорий книг
class Category(Base):
    __tablename__ = 'categories'

    id = Column(Integer, primary_key=True, index=True)
    # Код категории (уникальный)
    code = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)  # Название категории
    description = Column(String, nullable=False)  # Описание категории
    img = Column(String, nullable=False)  # Ссылка на картинку категории
    translations = Column(JSON, default={})  # Переводы названий
    # Связь с книгами
    books = relationship('Book', back_populates='category')


# 5. Модель книг
class Book(Base):
    __tablename__ = 'books'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))  # ID пользователя
    category_id = Column(Integer, ForeignKey('categories.id'))  # ID категории
    name_book = Column(String, nullable=False)  # Название книги
    description_book = Column(String, nullable=False, default='')
    content = Column(JSON, nullable=False)  # Содержание книги
    book_url = Column(String, nullable=False)  # Ссылка на книгу
    access_token = Column(String, nullable=True)  # Токен для загрузки книги

    # Связи
    user = relationship('User', back_populates='books')
    category = relationship('Category', back_populates='books')
    orders = relationship('Order', back_populates='book')


# Создание всех таблиц
Base.metadata.create_all(bind=engine)
