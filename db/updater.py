# db/updater.py
import logging

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import ProgrammingError
from db.models import Base
from .models import DATABASE_URL


# Функция для проверки и добавления столбцов
def check_and_update_database():
    # Создаем подключение к БД
    engine = create_engine(DATABASE_URL)
    inspector = inspect(engine)

    # Перебираем все таблицы из моделей
    for table_name, model in Base.metadata.tables.items():
        # Получаем список существующих столбцов в таблице
        existing_columns = {col['name']
                            for col in inspector.get_columns(table_name)}

        # Перебираем все столбцы модели
        for column in model.columns:
            column_name = column.name

            # Если столбца нет в БД
            if column_name not in existing_columns:
                # Получаем тип данных (например, INTEGER, VARCHAR)
                column_type = str(column.type).upper()

                # Формируем SQL-запрос для добавления столбца
                alter_query = f"ALTER TABLE {table_name} ADD COLUMN {
                    column_name} {column_type};"
                logging.warning(f"Добавление столбца '{
                                column_name}' в таблицу '{table_name}'.")

                # Выполняем запрос
                try:
                    with engine.connect() as conn:
                        conn.execute(text(alter_query))  # Выполняем SQL-запрос
                    logging.info(f"Столбец '{column_name}' добавлен в таблицу '{
                                 table_name}'.")
                except ProgrammingError as e:
                    logging.error(f"Ошибка добавления столбца '{
                                  column_name}': {e}")

    # Закрываем подключение
    engine.dispose()
