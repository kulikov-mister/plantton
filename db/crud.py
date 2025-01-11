# db/crud/crud.py
import json
from datetime import datetime, timedelta
from db.models import User, Payment, Order, Category, Book
from sqlalchemy.orm import Session
from utils.cache_utils import CacheManager


def dict_to_model(model_class, data: dict):
    """Преобразовать словарь данных в объект SQLAlchemy модели."""
    return model_class(**data)


class UserCRUD:
    cache = CacheManager()

    @staticmethod
    async def create_user(session: Session, user_id: str) -> User:
        """Создать нового пользователя и добавить его в кеш."""
        user = User(user_id=user_id)
        session.add(user)
        session.commit()
        session.refresh(user)

        # Сохраняем в кеш
        await UserCRUD.cache.set_data(user_id, {
            "id": user.id,
            "user_id": user.user_id,
            "balance": user.balance,
        })
        return user

    @staticmethod
    async def get_user_by_user_id(session: Session, user_id: str) -> User:
        """Получить пользователя из кеша или БД, возвращая SQLAlchemy объект."""
        # Пробуем получить данные из кеша
        cached_user = await UserCRUD.cache.get_data(user_id)
        if cached_user:
            return dict_to_model(User, cached_user)

        # Если нет в кеше, берем из БД и добавляем в кеш
        user = session.query(User).filter(User.user_id == user_id).first()
        if user:
            await UserCRUD.cache.set_data(user_id, {
                "id": user.id,
                "user_id": user.user_id,
                "pro": user.pro,
                "balance": user.balance,
                "charge_id": user.charge_id
            })
        return user

    @staticmethod
    async def update_user(session: Session, user_id: str, **kwargs) -> User:
        """Обновить данные пользователя в БД и кеше."""
        user = session.query(User).filter(User.user_id == user_id).first()
        if user:
            for key, value in kwargs.items():
                setattr(user, key, value)
            session.commit()
            session.refresh(user)

            # Обновляем кеш
            await UserCRUD.cache.update_data(user_id, kwargs)
        return user

    @staticmethod
    async def update_balance(session: Session, user_id: str, amount: int) -> User:
        """Обновить баланс пользователя в БД и сбросить кеш."""
        user = session.query(User).filter(User.user_id == user_id).first()
        if user:
            user.balance += amount  # Добавляем сумму к текущему балансу
            session.commit()
            session.refresh(user)

            # Сбрасываем кеш, чтобы избежать устаревших данных
            await UserCRUD.cache.delete(user_id)
        return user

    @staticmethod
    async def update_balance_down(session: Session, user_id: str, amount: int) -> User:
        """Обновить баланс пользователя в БД и сбросить кеш."""
        user = session.query(User).filter(User.user_id == user_id).first()
        if user:
            user.balance -= amount  # Отнимаем сумму
            session.commit()
            session.refresh(user)

            # Сбрасываем кеш, чтобы избежать устаревших данных
            await UserCRUD.cache.delete(user_id)
        return user

    @staticmethod
    async def update_status(session: Session, user_id: str, status: bool, days: int = None, charge_id: str = "") -> User:
        """Обновить статус пользователя в БД и сбросить кеш."""
        user = session.query(User).filter(User.user_id == user_id).first()
        if user:
            user.pro = status  # Обновляем баланс
            if days:
                user.date = datetime.now() + timedelta(days=days)  # Прибавляем дни

            # обновить id подписки
            user.charge_id = charge_id

            session.commit()
            session.refresh(user)

            # Сбрасываем кеш, чтобы избежать устаревших данных
            await UserCRUD.cache.delete(user_id)
        return user

    @staticmethod
    async def delete_user(session: Session, user_id: str) -> bool:
        """Удалить пользователя из БД и кеша."""
        user = session.query(User).filter(User.user_id == user_id).first()
        if user:
            session.delete(user)
            session.commit()

            # Удаляем из кеша
            await UserCRUD.cache.delete(user_id)
            return True
        return False


class PaymentCRUD:
    @staticmethod
    async def create_payment(session: Session, user_id: str, amount: float, charge_id: str) -> Payment:
        """Создать запись о пополнении баланса и сбросить кеш пользователя."""
        # Создаём запись о платеже
        payment = Payment(
            user_id=int(user_id), amount=amount, charge_id=charge_id
        )
        session.add(payment)
        session.commit()
        session.refresh(payment)

        # Обновляем баланс пользователя через UserCRUD со сбросом кеша
        await UserCRUD.update_balance(session, user_id, amount)

        return payment

    @staticmethod
    async def create_payment_with_update_status(
        session: Session, user_id: str, amount: float, charge_id: str, status: bool, days: int
    ) -> Payment:
        """Создать запись о пополнении баланса и не сбросить кеш пользователя."""
        # Создаём запись о платеже
        payment = Payment(
            user_id=int(user_id), amount=amount, charge_id=charge_id
        )
        session.add(payment)
        session.commit()
        session.refresh(payment)

        # Обновляем статус пользователя (сброс кэша внутри метода)
        user = await UserCRUD.update_status(session, user_id, status, days, charge_id)

        return payment

    @staticmethod
    async def get_payments_by_user_id(session: Session, user_id: str) -> Payment:
        """Получить список пополнений пользователя."""
        return session.query(Payment).filter(Payment.user_id == user_id).all()

    @staticmethod
    async def get_payment_by_charge_id(session: Session, charge_id: str) -> Payment:
        """Получить транзакцию пользователя по id транзакции."""
        return session.query(Payment).filter(Payment.charge_id == charge_id).first()

    @staticmethod
    async def update_refunded_payment_by_charge_id(session: Session, charge_id: str, status: bool) -> bool:
        """Получить транзакцию пользователя по id транзакции."""

        payment = session.query(Payment).filter(
            Payment.charge_id == charge_id).first()
        if payment:
            payment.refunded = status
            session.commit()
            session.refresh(payment)
            return payment

        return False

    @staticmethod
    async def delete_payment(session: Session, payment_id: int) -> bool:
        """Удалить запись о пополнении."""
        payment = session.query(Payment).filter(
            Payment.id == payment_id).first()
        if payment:
            session.delete(payment)
            session.commit()
            return True
        return False


class OrderCRUD:

    @staticmethod
    async def create_order(session: Session, user_id: int, book_id: int, amount: int, book_url: str) -> Order:
        """Создать новый заказ."""
        # Получаем пользователя
        user = session.query(User).filter(User.user_id == user_id).first()

        # Проверка на существование пользователя
        if user is None:
            raise ValueError(f"Пользователь с ID {user_id} не найден.")

        # Проверка баланса пользователя
        if user.balance is None:
            raise ValueError(f"Баланс пользователя с ID {
                             user_id} не установлен.")

        # Проверяем достаточно ли средств
        if user.balance < amount:
            raise ValueError("Недостаточно средств для создания заказа.")

        # Вычитаем сумму из баланса
        user.balance -= amount
        session.commit()
        session.refresh(user)

        # Сбрасываем кеш пользователя
        await UserCRUD.cache.delete(user_id)

        # Создаем заказ
        order = Order(
            user_id=user_id, book_id=book_id, amount=amount, book_url=book_url
        )
        session.add(order)
        session.commit()
        session.refresh(order)

        return order

    @staticmethod
    async def get_orders_by_user_id(session: Session, user_id: int):
        """Получить список заказов пользователя."""
        return session.query(Order).filter(Order.user_id == user_id).all()

    @staticmethod
    async def get_order_by_id(session: Session, order_id: int):
        """Получить заказ по ID."""
        return session.query(Order).filter(Order.id == order_id).first()

    @staticmethod
    async def delete_order(session: Session, order_id: int) -> bool:
        """Удалить заказ."""
        order = session.query(Order).filter(Order.id == order_id).first()
        if order:
            session.delete(order)
            session.commit()
            return True
        return False


class CategoryCRUD:
    cache = CacheManager()

    @staticmethod
    async def create_category(session: Session, name: str, translations: dict) -> Category:
        """Создать категорию и добавить в кеш."""
        category = Category(name=name, translations=translations)
        session.add(category)
        session.commit()
        session.refresh(category)

        # Добавляем в кеш
        await CategoryCRUD.cache.set_data(str(category.id), {
            "id": category.id,
            "name": category.name,
            "translations": category.translations
        })
        return category

    @staticmethod
    async def get_category_by_id(session: Session, category_id: int) -> Category:
        """Получить категорию из кеша или БД."""
        cached_category = await CategoryCRUD.cache.get_data(str(category_id))
        if cached_category:
            return dict_to_model(Category, cached_category)

        # Если в кеше нет, берем из БД
        category = session.query(Category).filter(
            Category.id == category_id).first()
        if category:
            await CategoryCRUD.cache.set_data(str(category.id), {
                "id": category.id,
                "name": category.name,
                "translations": category.translations
            })
        return category

    @staticmethod
    async def get_all_categories(session: Session) -> Category:
        """Получить все категории (с кешем)."""

        # Пробуем получить данные из кеша
        cached_categories = await CategoryCRUD.cache.get_data("all_categories")
        if cached_categories:
            # Возвращаем данные из кеша в виде списка объектов Category
            return [dict_to_model(Category, cat) for cat in cached_categories]

        # Если в кеше данных нет, берем из БД
        categories = session.query(Category).all()

        # Преобразуем категории в список словарей для кеширования
        categories_data = []
        for category in categories:
            categories_data.append({
                "id": category.id,
                "code": category.code,
                "name": category.name,
                "description": category.description,
                "img": category.img,
                "translations": category.translations
            })

        # Сохраняем в кеш
        await CategoryCRUD.cache.set_data("all_categories", categories_data)

        # Возвращаем объекты категорий
        return categories

    @staticmethod
    async def update_category(session: Session, category_id: int, **kwargs) -> Category:
        """Обновить категорию в БД и кеше."""
        category = session.query(Category).filter(
            Category.id == category_id).first()
        if category:
            for key, value in kwargs.items():
                setattr(category, key, value)
            session.commit()
            session.refresh(category)

            # Обновляем кеш
            await CategoryCRUD.cache.update_data(str(category_id), kwargs)
        return category

    @staticmethod
    async def delete_category(session: Session, category_id: int) -> bool:
        """Удалить категорию из БД и кеша."""
        category = session.query(Category).filter(
            Category.id == category_id).first()
        if category:
            session.delete(category)
            session.commit()

            # Удаляем из кеша
            await CategoryCRUD.cache.delete(str(category_id))
            return True
        return False


class BookCRUD:
    cache = CacheManager()

    @staticmethod
    async def create_book(
            session: Session, user_id: int, name_book: str, content: dict, book_url: str, access_token: str, price: int, category_id: int
    ) -> Book:
        """Создать книгу, создать заказ и обновить баланс."""
        # Создаем книгу
        book = Book(
            user_id=user_id, name_book=name_book, content=content,
            book_url=book_url, access_token=access_token, category_id=category_id
        )
        session.add(book)
        session.commit()
        session.refresh(book)

        # Создаем заказ и обновляем баланс (проверка уже в OrderCRUD)
        await OrderCRUD.create_order(session, user_id, book.id, price, book_url)

        # Добавляем книгу в кеш
        await BookCRUD.cache.set_data(str(book.id), {
            "id": book.id,
            "user_id": book.user_id,
            "name_book": book.name_book,
            "content": book.content,
            "book_url": book.book_url,
            "access_token": book.access_token
        })

        return book

    @staticmethod
    async def get_book_by_id(session: Session, book_id: int) -> Book:
        """Получить книгу из кеша или БД."""
        cached_book = await BookCRUD.cache.get_data(str(book_id))
        if cached_book:
            return dict_to_model(Book, cached_book)

        # Если в кеше нет, берем из БД
        book = session.query(Book).filter(Book.id == book_id).first()
        if book:
            await BookCRUD.cache.set_data(str(book.id), {
                "id": book.id,
                "user_id": book.user_id,
                "name_book": book.name_book,
                "content": book.content,
                "book_url": book.book_url,
                "access_token": book.access_token
            })
        return book

    @staticmethod
    async def get_books_by_user_id(session: Session, user_id: int):
        """Получить все книги пользователя (без кеша)."""
        cached_books = await BookCRUD.cache.get_data('books_'+user_id)
        if cached_books:
            return dict_to_model(Book, cached_books)

        books = session.query(Book).filter(Book.user_id == user_id).all()
        result = [
            {
                "id": book.id,
                "name_book": book.name_book,
                "description_book": book.description_book,
                "book_url": book.book_url,
            }
            for book in books
        ]
        await BookCRUD.cache.set_data(f'books_{user_id}', result)
        return result

    @staticmethod
    async def get_all_books_by_category_code(session: Session, category_code: str):
        """Получить все книги по коду категории."""
        cached_books = await BookCRUD.cache.get_data(f'#c_{category_code}')
        if cached_books:
            return dict_to_model(Book, cached_books)

        # Получаем категорию по коду
        category = session.query(Category).filter(
            Category.code == category_code).first()
        if not category:
            return []

        # Получаем книги, связанные с категорией
        books = session.query(Book).filter(
            Book.category_id == category.id).all()

        result = [
            {
                "id": book.id,
                "title": book.name_book,
                "description": book.description_book or 'Нет описания',
                "image_url": "https://i.imgur.com/Dnm3RRZ.png",
                "book_url": book.book_url,
            }
            for book in books
        ]

        if result:
            await BookCRUD.cache.set_data(f'#c_{category_code}', result)
        return result

    @staticmethod
    async def update_book(session: Session, book_id: int, **kwargs) -> Book:
        """Обновить книгу в БД и кеше."""
        book = session.query(Book).filter(Book.id == book_id).first()
        if book:
            for key, value in kwargs.items():
                setattr(book, key, value)
            session.commit()
            session.refresh(book)

            # Обновляем кеш
            await BookCRUD.cache.update_data(str(book_id), kwargs)
        return book

    @staticmethod
    async def delete_book(session: Session, book_id: int) -> bool:
        """Удалить книгу из БД и кеша."""
        book = session.query(Book).filter(Book.id == book_id).first()
        if book:
            session.delete(book)
            session.commit()

            # Удаляем из кеша
            await BookCRUD.cache.delete(str(book_id))
            return True
        return False
