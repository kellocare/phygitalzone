import telebot
import sqlite3
from datetime import datetime
from telebot import types
import threading

# Инициализация бота
bot = telebot.TeleBot("6984068979:AAEw5WSw-AC7qYcAr4IjiNe6dfNshMCBcYk")

# Подключение к базе данных SQLite
conn = sqlite3.connect('users.db', check_same_thread=False)
cursor = conn.cursor()

# Создание таблицы для хранения пользователей, если она еще не существует
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        registration_date TEXT,
        participation_count INTEGER
    )
''')
conn.commit()

# Mutex для блокировки доступа к базе данных из разных потоков
db_lock = threading.Lock()

# Обработчик команды /start
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    with db_lock:
        cursor.execute('SELECT * FROM users WHERE user_id=?', (user_id,))
        user_data = cursor.fetchone()
    if user_data:
        show_profile(message)
    else:
        markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
        register_button = types.KeyboardButton("🎮 Зарегистрироваться")
        markup.add(register_button)
        bot.send_message(message.chat.id, "Привет! Нажмите кнопку 'Зарегистрироваться', чтобы начать.", reply_markup=markup)

# Обработчик кнопки "Зарегистрироваться"
@bot.message_handler(func=lambda message: message.text == "🎮 Зарегистрироваться")
def register(message):
    user_id = message.from_user.id
    with db_lock:
        cursor.execute('SELECT * FROM users WHERE user_id=?', (user_id,))
        user_data = cursor.fetchone()
        if not user_data:
            username = message.from_user.username
            registration_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute('INSERT INTO users (user_id, username, registration_date, participation_count) VALUES (?, ?, ?, ?)',
                           (user_id, username, registration_date, 0))
            conn.commit()
            bot.reply_to(message, "Вы успешно зарегистрированы! 🎉")
            hide_registration_button(message.chat.id, message.message_id)
            show_profile_button(message.chat.id)
        else:
            bot.reply_to(message, "Вы уже зарегистрированы. 🕹️")

# Обработчик кнопки "Мой профиль"
@bot.message_handler(func=lambda message: message.text == "📂 Мой профиль")
def show_profile(message):
    user_id = message.from_user.id
    with db_lock:
        cursor.execute('SELECT * FROM users WHERE user_id=?', (user_id,))
        user_data = cursor.fetchone()
    if user_data:
        user_info = user_data
        profile_text = (
            f"🆔 ID: {user_info[0]}\n"
            f"👤 Username: @{user_info[1]}\n"
            f"📅 Дата регистрации: {user_info[2]}\n"
            f"🎮 Количество участий в мероприятиях: {user_info[3]}"
        )
        bot.reply_to(message, profile_text)
    else:
        bot.reply_to(message, "Вы еще не зарегистрированы. Нажмите кнопку 'Зарегистрироваться'.")

# Функция для отправки кнопки "Мой профиль"
def show_profile_button(chat_id):
    markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    profile_button = types.KeyboardButton("📂 Мой профиль")
    markup.add(profile_button)
    bot.send_message(chat_id, "Теперь вы можете просмотреть свой профиль. 🎮", reply_markup=markup)

# Функция для удаления кнопки "Зарегистрироваться"
def hide_registration_button(chat_id, message_id):
    bot.delete_message(chat_id, message_id)

# Запуск бота
bot.polling()

# Закрытие соединения с базой данных после остановки бота
conn.close()
