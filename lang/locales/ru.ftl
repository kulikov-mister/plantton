# ###################### СООБЩЕНИЯ #############################

start_message = <b>Привет! Твой баланс: {$balance}</b>

help_message = 
    <b>Привет! вот список команд:</b>
    
    /start - старт бота 🚀
    /help - список команд 📋
    /create_book - создать книгу 📚
    /books - библиотека 📓📔📒📕📗📘📙
    /balance - проверить баланс 📈
    /add_balance - пополнить баланс 👛
    /pro - управление подпиской 😎
    /close - закончить операцию ❌
    /privacy = Политика конфиденциальности 📃
    /terms = Условия использования 📄

greeting_message =
    🌟 Наш бот <b>App 5</b> в Telegram - это образовательная система для создания маленьких книг как для учеников школ, так и для студентов.

    💡 <b>App 5</b> максимально прост и удобен в использовании, с поддержкой нескольких языков.

    📈 Присоединяйтесь к нашему <b><a href="https://t.me/app5_news">каналу</a></b>, чтобы быть в курсе новостей!


not_user_message = 
    <b>Вы не зарегистрированы!</b>

    <i>/start для регистрации</i>

registration_success = <b>🎉 Теперь Вы пользователь App 5! 🎉</b>

balance_message = 
    <b>Привет! Вот информация по балансу:</b>
      - <b>Баланс:</b> {$balance}
      - <b>Статус:</b> {$pro}
    
    <i>/add_balance для пополнения</i> 👛

low_balance = 
    ⚠️ <b>Для использования этой функции баланс должен быть больше:</b> <u>{$limit}</u>
      - <b>Ваш баланс:</b> {$balance}
      - <b>Статус:</b> {$pro}
    
    <i>/add_balance для пополнения</i> 👛


cancelled_message = ❌ Отменено!
close_message = ❌ Отменено!
    
    <i>/help - список команд.</i>

set_query_book =
    🖐 <b>Создаём книгу вот с такими данными:</b>
    
    <b>Тема:</b> {$query_book}
    <b>Категория:</b> {$category_str}
    <b>Количество глав:</b> {$qt_topics}

    <i>Нажмите чтобы продолжить </i>

next_btn = Продолжить ➡️
next_topics_btn = Другое содержание 🔄
close_btn = Закрыть ❌
restart_pro_btn = 🌟 Возобновить подписку 🌟
cancel_pro_btn = 😢 Остановить подписку..

create_book_message =
    🖐 Привет, Я - <b>App 5!</b>

    <blockquote>
    <b>Я создаю микро-книги на академическую тематику и загружаю их в Telegraph.</b>

    - Меня можно использовать для обучения, чтобы быстро создать учебный материал и предоставить его аудитории в удобном формате.
    </blockquote>
    <b>Сейчас Вам предстоит:</b>
      - выбрать категорию,
      - ввести желаемое количество глав,
      - придумать название для новой главы.

create_book_message_1 = 1️⃣ <b>Сначала выберите категорию для новой микрокниги:</b>
create_book_message_2 = 2️⃣ <b>Напишите количество глав для новой микрокниги от 1 до 10:</b>
create_book_message_2_err = ⚠️ <b>Количество глав должно быть от 1 до 10!</b>
create_book_message_3 = 3️⃣ <b>И наконец, напишите мне тему для новой микрокниги:</b>

topics_message =
    <b>Вот список глав для новой книги:</b>

    {$topics_text}

topics_message_error = ⚠️ <b>Не удалось получить список глав..</b>
start_generating_book_message = 
    1️⃣ <b>Начало генерации книги.</b>
    Создание книги состоит из 2-х этапов:
      - Генерация содержания книги.
      - Загрузка книги в Telegraph.

    <i>Этот шаг может занять до 5 минут!</i>

end_generating_book_message = 
    2️⃣ <b>Начало загрузки книги в Telegraph.</b>
    
    <i>Этот шаг может занять до 2 минут!</i>

order_create_message_ok = 
    ✅ <b>Создание книги успешно завершено!</b>
    С Вашего баланса списано: {$price} 🌟!

generating_book_message_err = ⚠️ <b>Не удалось создать книгу в Telegraph..</b>
generating_book_empty_message = ⚠️ <b>Книга не создана или пустая..</b>
book_create_error = ⚠️ <b>Ошибка добавления книги в бд</b>
book_create_error_admin =
    ⚠️ <b>Ошибка добавления книги в бд у пользователя {$user_id}</b>
    
    { $msg_book }

generate_topics_book_error =
    ⚠️ <b>Ошибка генерации содержания книги!</b>
    
    <i>{ $error }</i>
    

callback_empty_message = ⚠️ Повторите попытку заново
pagination_answer = Страница { $page }
no_categories = ⭕️ <b>Нет категорий</b>
create_book_no_categories = ⭕️ <b>Нет категорий в которой можно было бы создать кингу...</b>


# ###################### ИНЛАЙН РЕЖИМ #############################

choose_category = <b>Выберите категорию:</b> 👇
choose_book = <b>Выберите книгу:</b> 👇

no_more_results = ⭕️ Нет результатов
no_more_results_description = 🤷‍♂️ Книг не найдено

code_404_description = Ошибка: неверный код капчи!
code_404 = Ошибка 404
switch_pm_text_categories = Добавить ещё »»
switch_pm_text_start = Вернуться в главное меню 🚀
switch_pm_text_books = ◀️ Вернуться к списку категорий

switch_pm_text_register = Зарегистрироваться в один клик ⚡️
not_user_description = Зарегистрируйтесь, чтобы использовать App 5!
not_user_title = 🤷‍♂️ Вы не зарегистрированы

description_part_1 = Книга:

# ###################### НАСТРОЙКИ БОТА #############################

settings_message = настройки

start_cmd_description = Старт 🚀
help_cmd_description = Список команд 📋
create_book_cmd_description = Создать книгу 📚
books_cmd_description = Библиотека 📓📔📒📕📗📘📙
close_cmd_description = Закончить 🙅‍♂️
balance_cmd_description = Проверить баланс 📈
pro_cmd_description = Статус Pro 😎
privacy_cmd_description = Политика конфиденциальности 📃
terms_cmd_description = Условия использования 📄

bot_name = Приложение 5

bot_description =
    Я создаю микро-книги на академическую тематику и загружаю их в Telegraph. 🌟

    Меня используют для обучения, чтобы быстро создать учебный материал и предоставить его аудитории в удобном формате.

bot_short_description =
    Я создаю микро-книги на академическую тематику и загружаю их в Telegraph. 🌟




# ###################### ПЛАТЕЖИ #############################
# ###################### ПЛАТЕЖИ #############################

# ###################### КАТЕГОРИИ #############################



# ###################### ПЛАТЕЖИ #############################
cmd_add_balance_message = <b>Введите количество звёзд, на которое Вы хотите пополнить баланс.</b> 👇
new_invoice_message_text_err = <b>Введите число звёзд от 1 до 10000.</b>
invoice_message_err = 😢 Что-то пошло не так, повторите попытку позже..
new_invoice_btn_text = Пополнить на { $amount } ⭐️
new_invoice_title = Пополнение баланса на { $amount } ⭐️
new_invoice_description = Пополнение баланса в Приложение 5 на { $amount } ⭐️!

status_pro_btn_text = Статус Pro за { $amount } ⭐️
status_pro_title = Cтатус Pro!
status_pro_description = Покупка статуса Pro за { $amount } ⭐️ на 30 дней.
pro_status_already = 🤗 <b>Ваш статус Pro активен!</b>
pro_status_inactive = 🖐 <b>Ваш статус Pro не активен!</b>

status_pro_success = 🥳 <b>Спасибо, Ваш статус Pro успешно активирован!</b> 🤗
restart_pro_success = 🥳 <b>Спасибо, Ваш статус Pro восстановлен!</b> 🤗
cancel_pro_success = 😢 <b>Ваш статус Pro успешно деактивирован..</b>

status_pro_restart_process = 🤗 <b>Возобновляю подписку на статус Pro..</b>
subscription_not_active_restart = ⚠️ <b>Подписка не активна! Создайте новую</b>
subscription_not_active_err = ⚠️ <b>Подписка не активна! Создайте новую!</b>

error_pro_no_charge_id = ⚠️ <b>Подписка активна! Но нет ID транзакции!</b>
subscription_not_modified = ⚠️ <b>Подписка не может быть изменена или уже активна!</b>

status_pro_restart_process_err =
    ⚠️ <b>Ошибка отмены подписки -</b>
    
    <i>{ $error }</i>

new_invoice_message_success =
    🥳 <b>Спасибо, Ваша транзакция успешно прошла!</b> 🤗
    
    <i>Баланс пополнен на { $amount } ⭐️. Остаток: { $balance } ⭐️</i>

balance_updated = 😢 <b>Баланс понижен  на { $amount } ⭐️. Остаток: { $balance } ⭐️</b>
refund_stars_success = 
    🤗 <b>Успешно выполнен возврат средств:</b>
    
    <b>Количество:</b> <i>{ $total_amount }</i> ⭐️!
    <b>ID транзакции:</b> <i>{ $charge_id }</i>!

refund_payment_none_message = 😢 <b>Транзакция не найдена..</b>
refund_star_payment_err = 😢 <b>Не удалось обновить статус возврата транзакции в базе данных..</b>
payment_creation_error = 😢 <b>При создании платежа возникла проблема..</b>


# ###################### ДОНАТЫ #############################
cmd_donate_message = <b>Введите количество звёзд, которое Вы хотите задонатить..</b> 👇
donate_message_success = 🥳 Спасибо за вашу поддержку! 🤗
donate_message_text_err = <b>Введите число звёзд от 1 до 10000.</b>
donate_btn_text = Отправить {$amount_stars} ⭐️
donate_invoice_title = ❤️ Донат для Приложение 5 ❤️
donate_invoice_description = Поддержка App 5 на {amount_stars} ⭐️!


# ###################### ПРОМТЫ #############################
prompt_topics =
    Напиши список из {$qt_topics} глав для книги на тему: {$query_topics}.
    Используй list схему:
    [ "глава 1", "глава 2", ..., "глава {$qt_topics}"]
    Верни чистый список без форматирования и лишних символов - [...]

prompt_topic =
    Мы пишем книгу на тему: {$query_topics}.
    Сейчас напиши подробно главу для этой книги на тему {$bt}.
    Не используй слово - "Глава ..." и прочую нумерацию в своём ответе, чтобы не было путаницы.
    Используй обязательно частое форматирование для украшения и читаемости главы.
    Верни только текст главы с форматированием без лишних символов.