# db/updater.py
import logging
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import SQLAlchemyError
from db.models import Base, DATABASE_URL

logging.basicConfig(level=logging.INFO)


def sync_database():
    """
    Синхронизирует базу данных с текущими моделями:
    - Добавляет отсутствующие столбцы.
    - Удаляет лишние таблицы и столбцы.
    - Сохраняет данные при миграциях.
    """
    engine = create_engine(DATABASE_URL)
    inspector = inspect(engine)

    # Получаем список существующих таблиц в базе данных
    existing_tables = inspector.get_table_names()

    # Удаление лишних таблиц, которых нет в моделях
    for table_name in existing_tables:
        if table_name not in Base.metadata.tables:
            logging.warning(
                f"Таблица '{table_name}' отсутствует в моделях. Удаляем...")
            with engine.connect() as conn:
                conn.execute(text(f"DROP TABLE IF EXISTS {table_name}"))
            logging.info(f"Таблица '{table_name}' удалена.")

    # Синхронизация таблиц, указанных в моделях
    for table_name, model_table in Base.metadata.tables.items():
        if table_name in existing_tables:
            # Таблица существует, проверяем столбцы
            logging.info(
                f"Таблица '{table_name}' существует. Проверяем столбцы...")
            existing_columns = {
                col["name"]: col for col in inspector.get_columns(table_name)}

            for column in model_table.columns:
                column_name = column.name

                if column_name not in existing_columns:
                    # Добавляем отсутствующий столбец
                    column_type = str(column.type).upper()
                    logging.warning(f"Добавление столбца '{
                                    column_name}' в таблицу '{table_name}'...")
                    alter_query = f"ALTER TABLE {table_name} ADD COLUMN {
                        column_name} {column_type}"
                    try:
                        with engine.connect() as conn:
                            conn.execute(text(alter_query))
                        logging.info(f"Столбец '{column_name}' добавлен в таблицу '{
                                     table_name}'.")
                    except SQLAlchemyError as e:
                        logging.error(f"Ошибка добавления столбца '{
                                      column_name}': {e}")
                elif str(existing_columns[column_name]["type"]).upper() != str(column.type).upper():
                    # Пересоздаем столбец с сохранением данных, если его тип не совпадает
                    logging.warning(f"Тип столбца '{column_name}' в таблице '{
                                    table_name}' отличается. Пересоздаем столбец...")
                    temp_column_name = f"{column_name}_temp"
                    try:
                        with engine.connect() as conn:
                            # Добавляем временный столбец
                            conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {
                                         temp_column_name} {column.type}"))
                            # Копируем данные из старого столбца
                            conn.execute(text(f"UPDATE {table_name} SET {
                                         temp_column_name} = {column_name}"))
                            # Удаляем старый столбец
                            conn.execute(text(f"PRAGMA foreign_keys=off"))
                            conn.execute(
                                text(f"ALTER TABLE {table_name} RENAME TO {table_name}_backup"))
                            model_table.create(engine)
                            columns = ", ".join(
                                [col.name for col in model_table.columns])
                            conn.execute(
                                text(f"INSERT INTO {table_name} ({columns}) SELECT {
                                     columns} FROM {table_name}_backup")
                            )
                            conn.execute(
                                text(f"DROP TABLE {table_name}_backup"))
                            conn.execute(text(f"PRAGMA foreign_keys=on"))
                        logging.info(f"Столбец '{column_name}' пересоздан в таблице '{
                                     table_name}'.")
                    except SQLAlchemyError as e:
                        logging.error(f"Ошибка пересоздания столбца '{
                                      column_name}': {e}")
        else:
            # Если таблицы нет, создаем её
            logging.info(f"Создаем таблицу '{table_name}'...")
            try:
                model_table.create(engine)
                logging.info(f"Таблица '{table_name}' создана.")
            except SQLAlchemyError as e:
                logging.error(f"Ошибка создания таблицы '{table_name}': {e}")

    # Закрываем подключение к базе данных
    engine.dispose()


if __name__ == "__main__":
    sync_database()
