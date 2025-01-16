# db/crud/crud.py
import json
from datetime import datetime, timedelta
from db.models import User, Payment, Category, Book
from sqlalchemy.orm import Session
from utils.cache_utils import CacheManager
from utils.code_generator import generate_random_string_async_lower

cache = CacheManager()


# TODO: переписать все классы под единую функцию-обёртку объединяющую работу с кешем
class UserCRUD:

    @staticmethod
    async def create_user(session: Session, user_id: str, charge_id: str = '') -> User:
        """Создать нового пользователя и добавить его в кеш."""
        user = User(user_id=user_id, charge_id=charge_id)
        session.add(user)
        session.commit()
        session.refresh(user)

        # Сохраняем в кеш
        await cache.set_data(user_id, User.to_dict(user))
        return user

    @staticmethod
    async def get_user_by_user_id(session: Session, user_id: str) -> User:
        """Получить пользователя из кеша или БД."""
        cached_user = await cache.get_data(user_id)
        if cached_user:
            return User.from_dict(cached_user)

        # Если в кеше нет, берем из БД
        user = session.query(User).filter(User.user_id == user_id).first()
        if user:
            await cache.set_data(user_id, User.to_dict(user))
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

            # Обновляем данные в кеше
            await cache.update_data(user_id, kwargs)
        return user

    @staticmethod
    async def update_balance(session: Session, user_id: str, amount: int) -> User:
        """Обновить баланс пользователя в БД и сбросить кеш."""
        user = session.query(User).filter(User.user_id == user_id).first()
        if user:
            user.balance += amount
            session.commit()
            session.refresh(user)

            # Удаляем старые данные из кеша
            await cache.delete(user_id)
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
            await cache.delete(user_id)
        return user

    @staticmethod
    async def update_status(session: Session, user_id: str, status: bool, days: int = None, charge_id: str = "") -> User:
        """Обновить статус пользователя в БД и сбросить кеш."""
        user = session.query(User).filter(User.user_id == user_id).first()
        if user:
            user.pro = status
            if days:
                user.date = datetime.now() + timedelta(days=days)
            user.charge_id = charge_id
            session.commit()
            session.refresh(user)

            # Обновляем кеш
            await cache.delete(user_id)
        return user

    @staticmethod
    async def delete_user(session: Session, user_id: str) -> bool:
        """Удалить пользователя из БД и кеша."""
        user = session.query(User).filter(User.user_id == user_id).first()
        if user:
            session.delete(user)
            session.commit()

            # Удаляем из кеша
            await cache.delete(user_id)
            return True
        return False


class PaymentCRUD:

    @staticmethod
    async def create_payment(session: Session, user_id: str, amount: float, charge_id: str) -> Payment:
        """Создать запись о платеже и сбросить кеш пользователя."""
        payment = Payment(user_id=user_id, amount=amount, charge_id=charge_id)
        session.add(payment)
        session.commit()
        session.refresh(payment)

        # Обновляем баланс пользователя
        await UserCRUD.update_balance(session, user_id, amount)

        return payment

    @staticmethod
    async def create_payment_with_update_status(session: Session, user_id: str, amount: float, charge_id: str, status: bool, days: int) -> Payment:
        """Создать запись о пополнении баланса и сбросить кеш пользователя."""
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
    async def get_payments_by_user_id(session: Session, user_id: str):
        """Получить список платежей пользователя."""
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


class CategoryCRUD:

    @staticmethod
    async def create_category(session: Session, name: str, translations: dict, description: str = "", img: str = "") -> Category:
        """Создать категорию и добавить в кеш."""
        code = await generate_random_string_async_lower(4)
        category = Category(
            name=name, code=code, description=description, img=img, translations=translations)
        session.add(category)
        session.commit()
        session.refresh(category)

        # Добавляем в кеш
        await cache.set_data(str(category.id), {
            "id": category.id,
            "name": category.name,
            "translations": category.translations,
        })
        return category

    @staticmethod
    async def get_category_by_id(session: Session, category_id: int) -> Category:
        """Получить категорию из кеша или БД."""
        cached_category = await cache.get_data(str(category_id))
        if cached_category:
            return Category.from_dict(cached_category)

        # Если в кеше нет, берем из БД
        category = session.query(Category).filter(
            Category.id == category_id).first()
        if category:
            await cache.set_data(str(category.id), Category.to_dict(category))
        return category

    @staticmethod
    async def get_category_by_category_code(session: Session, category_code: str) -> Category:
        """Получить категорию из кеша или БД."""
        cache_key = f'category_by_{category_code}'

        cached_category = await cache.get_data(cache_key)
        if cached_category:
            return Category.from_dict(cached_category)

        # Если в кеше нет, берем из БД
        category = session.query(Category).filter(
            Category.code == category_code).first()
        if category:
            await cache.set_data(cache_key, Category.to_dict(category))
        return category

    @staticmethod
    async def get_all_categories(session: Session) -> Category:
        """Получить все категории (с кешем)."""
        cache_key = "all_categories"
        # Пробуем получить данные из кеша
        cached_categories = await cache.get_data(cache_key)
        if cached_categories:
            # Возвращаем данные из кеша в виде списка объектов Category
            return [Category.from_dict(cat) for cat in cached_categories]

        # Если в кеше данных нет, берем из БД
        categories = session.query(Category).all()

        # Преобразуем категории в список словарей для кеширования
        categories_data = [Category.to_dict(
            category) for category in categories]

        # Сохраняем в кеш
        await cache.set_data(cache_key, categories_data)

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
            await cache.update_data(str(category_id), kwargs)
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
            await cache.delete(str(category_id))
            return True
        return False


class BookCRUD:

    @staticmethod
    async def create_book(
        session: Session, user_id: str, name_book: str, content: dict, book_url: str, access_token: str, category_id: int
    ) -> Book:
        """Создать книгу."""
        # Создаём книгу
        book = Book(
            user_id=user_id, name_book=name_book, content=content,
            book_url=book_url, access_token=access_token, category_id=category_id
        )
        session.add(book)
        session.commit()
        session.refresh(book)

        # чистим кеш
        await cache.delete('all_books')

        return book

    @staticmethod
    async def get_all_books(session: Session) -> list[Book]:
        """Получить книгу из кеша или БД."""
        cache_key = "all_books"
        cached_books = await cache.get_data(cache_key)
        if cached_books:
            return [Book.from_dict(book_data) for book_data in cached_books]

        # Если в кеше нет, берем из БД
        books = session.query(Book).all()
        result = [book.to_dict() for book in books]
        await cache.set_data(cache_key, result)
        return books

    @staticmethod
    async def get_book_by_id(session: Session, book_id: int) -> Book:
        """Получить книгу из кеша или БД."""
        cached_book = await cache.get_data(str(book_id))
        if cached_book:
            return [Book.from_dict(cached_book)]

        # Если в кеше нет, берем из БД
        book = session.query(Book).filter(Book.id == book_id).first()
        if book:
            await cache.set_data(str(book.id), book.to_dict())
        return book

    @staticmethod
    async def get_books_by_user_id(session: Session, user_id: int) -> list[Book]:
        """Получить все книги пользователя (с поддержкой кеша)."""
        cache_key = f'books_{user_id}'
        cached_books = await cache.get_data(cache_key)
        # Если данные есть в кеше, преобразуем их в объекты модели Book
        if cached_books:
            return [Book.from_dict(book_data) for book_data in cached_books]

        # Если данных в кеше нет, получаем их из базы данных
        books = session.query(Book).filter(Book.user_id == user_id).all()

        # Преобразуем книги в список словарей и сохраняем в кеше
        result = [book.to_dict() for book in books]
        await cache.set_data(cache_key, result)

        # Преобразуем данные в список объектов модели Book перед возвратом
        return books

    @staticmethod
    async def get_all_books_by_category_code(session: Session, category_code: str) -> list[Book]:
        """
        Получить все книги по коду категории (с поддержкой кеша).
        """
        cache_key = f'books={category_code}'

        # Проверяем кеш
        cached_books = await cache.get_data(cache_key)
        if cached_books:
            return [Book.from_dict(book_data) for book_data in cached_books]

        # Получаем все книги (из кеша или БД)
        books = await BookCRUD.get_all_books(session)
        if not books:
            return []

        # Получаем категорию по коду
        category = await CategoryCRUD.get_category_by_category_code(session, category_code)

        if not category:
            return []

        # Фильтруем книги по id категории
        filtered_books = [
            book for book in books if str(book.category_id) == str(category.id)]

        if not filtered_books:
            return []

        # Преобразуем книги в список словарей
        result = [book.to_dict() for book in filtered_books]

        # Сохраняем результат в кеше
        await cache.set_data(cache_key, result)
        return filtered_books

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
        await cache.update_data(str(book_id), kwargs)
        return book

    @staticmethod
    async def delete_book(session: Session, book_id: int) -> bool:
        """Удалить книгу из БД и кеша."""
        book = session.query(Book).filter(Book.id == book_id).first()
        if book:
            session.delete(book)
            session.commit()

            # Удаляем из кеша
            await cache.delete(str(book_id))
            return True
        return False
