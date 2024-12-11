import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
import os
from datetime import datetime
import pandas as pd
import re
from telebot import apihelper
import time 
from datetime import datetime, timedelta
import threading

# Налаштування таймауту для всіх запитів
apihelper.CONNECT_TIMEOUT = 30  # Таймаут підключення
apihelper.READ_TIMEOUT = 30     # Таймаут читання відповіді

# Токен  бота
API_TOKEN = '7602893334:AAFMYoVxfDxgeQjmX68RX7Ri_4gGFMe2wlk'
bot = telebot.TeleBot(API_TOKEN, parse_mode=None)



# Функція для очищення імен
def sanitize_filename(name):
    # Видаляємо заборонені символи та зайві пробіли
    name = re.sub(r'[<>:"/\\|?*,]', '_', name)  # Заміняємо недопустимі символи
    return name.strip()  # Видаляємо зайві пробіли


# # Завантажуємо список користувачів та клієнтів з Excel
# def load_clients_from_excel(file_path):
#     df = pd.read_excel(file_path)
#     users = {}
    
#     for _, row in df.iterrows():
#         user = row['User']
#         client = row['Client']
        
#         if user not in users:
#             users[user] = []
#         users[user].append(client)
    
#     return users

# Завантажуємо користувачів і клієнтів з Excel
# USERS = load_clients_from_excel('clients.xls')  # Замість 'clients.xlsx' вкажіть свій шлях до файлу Excel

# Дані з Excel
EXCEL_FILE = 'clients.xls'  # Шлях до вашого файлу Excel

# Функція для завантаження даних з Excel
def load_clients_from_excel(file_path):
    df = pd.read_excel(file_path)
    data = {}

    for _, row in df.iterrows():
        region = row['Region']
        district = row['District']
        client = row['Client']

        if region not in data:
            data[region] = {}
        if district not in data[region]:
            data[region][district] = []
        data[region][district].append(client)

    return data

# Завантажуємо дані
CLIENTS = load_clients_from_excel(EXCEL_FILE)

# Базова папка для збереження фото
BASE_FOLDER = "user_client_photos"
os.makedirs(BASE_FOLDER, exist_ok=True)

# Стан для кожного користувача
user_state = {}
last_interaction_time = {}  # Відстеження останньої взаємодії з ботом
last_activity = {}
INACTIVITY_LIMIT = timedelta(hours=1)  # Часовий ліміт бездіяльності

# Функція перевірки активності
def check_inactivity():
    while True:
        now = datetime.now()
        for chat_id in list(last_interaction_time.keys()):
            if now - last_interaction_time[chat_id] > INACTIVITY_LIMIT:
                del last_interaction_time[chat_id]  # Видалення користувача після закінчення часу
                if chat_id in user_state:
                    del user_state[chat_id]
                try:
                    bot.send_message(chat_id, "Час бездіяльності завершено. Натисніть /start, щоб почати заново.")
                except Exception as e:
                    print(f"Помилка надсилання повідомлення: {e}")
        threading.Event().wait(60)  # Перевірка кожну хвилину

# Запуск перевірки бездіяльності у фоновому потоці
threading.Thread(target=check_inactivity, daemon=True).start()



# Функція для санітизації callback_data
def sanitize_callback_data(data):
    return data[:64]  # Обрізаємо до 64 символів

# # Хендлер для кнопки "Старт"
# @bot.message_handler(commands=['start'])
# def handle_start(message):
#     chat_id = message.chat.id
#     last_interaction_time[chat_id] = datetime.now()  # Оновлення часу останньої взаємодії
    
#     # Створюємо клавіатуру
#     markup = ReplyKeyboardMarkup(resize_keyboard=True)
#     start_button = KeyboardButton("Вибрати напрямок")  # Текст кнопки
#     markup.add(start_button)
    
#     bot.send_message(chat_id, "Натисніть 'Вибрати напрямок', щоб продовжити.", reply_markup=markup)

# # Хендлер для обробки натискання "Вибрати торгового"
# @bot.message_handler(func=lambda message: message.text == "Вибрати напрямок")
# def handle_start_button(message):
#     chat_id = message.chat.id
#     last_interaction_time[chat_id] = datetime.now()  # Оновлення часу останньої взаємодії
    

#     # Показати список користувачів
#     markup = InlineKeyboardMarkup()
#     for user in USERS.keys():
#         sanitized_data = sanitize_callback_data(f"user:{user}")
#         markup.add(InlineKeyboardButton(user, callback_data=sanitized_data))
#     bot.send_message(chat_id, "Оберіть напрямок:", reply_markup=markup)

# # Обробка вибору користувача
# @bot.callback_query_handler(func=lambda call: call.data.startswith("user:"))
# def handle_user_selection(call):
#     chat_id = call.message.chat.id
#     selected_user = call.data.split(":")[1]
#     last_interaction_time[chat_id] = datetime.now()  # Оновлення часу останньої взаємодії
    
#     # Збереження вибраного користувача
#     user_state[chat_id] = {'user': selected_user}
    
#     # Показати список клієнтів для вибраного користувача
#     markup = InlineKeyboardMarkup()
#     for client in USERS[selected_user]:
#         sanitized_data = sanitize_callback_data(f"client:{client}")
#         markup.add(InlineKeyboardButton(client, callback_data=sanitized_data))
#     bot.send_message(chat_id, f"Напрямок {selected_user} вибраний. Оберіть клієнта:", reply_markup=markup)

# # Обробка вибору клієнта
# @bot.callback_query_handler(func=lambda call: call.data.startswith("client:"))
# def handle_client_selection(call):
#     chat_id = call.message.chat.id
#     last_interaction_time[chat_id] = datetime.now()  # Оновлення часу останньої взаємодії
#     selected_client = call.data.split(":")[1]
    
#     # # Збереження вибраного клієнта
#     # user_state[chat_id]['client'] = selected_client
    
#     # bot.send_message(chat_id, f"Клієнт {selected_client} вибраний. Тепер завантажте фото.")
#       # Перевіряємо, чи існує запис для користувача
#     if chat_id not in user_state or 'user' not in user_state[chat_id]:
#         bot.send_message(chat_id, "Будь ласка, спочатку оберіть напрямок за допомогою команди /start.")
#         return

#     # Додаємо вибраного клієнта в стан користувача
#     user_state[chat_id]['client'] = selected_client
    
#     bot.send_message(chat_id, f"Клієнт {selected_client} вибраний. Тепер завантажте фото.")

# Функція для створення головної клавіатури
def create_main_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    button = KeyboardButton("Вибрати напрямок")
    markup.add(button)
    return markup

# Хендлер для команди /start
@bot.message_handler(commands=['start'])
def handle_start(message):
    chat_id = message.chat.id
    last_activity[chat_id] = datetime.now()
    bot.send_message(chat_id, "Натисніть 'Вибрати напрямок', щоб продовжити.", reply_markup=create_main_keyboard())

# Хендлер для кнопки "Вибрати напрямок"
@bot.message_handler(func=lambda message: message.text == "Вибрати напрямок")
def handle_select_region(message):
    chat_id = message.chat.id
    last_activity[chat_id] = datetime.now()
    user_state[chat_id] = {}

    # Показати список областей
    markup = InlineKeyboardMarkup()
    for region in CLIENTS.keys():
        markup.add(InlineKeyboardButton(region, callback_data=f"region:{region}"))
    bot.send_message(chat_id, "Оберіть область:", reply_markup=markup)

# Обробка вибору області
@bot.callback_query_handler(func=lambda call: call.data.startswith("region:"))
def handle_region_selection(call):
    chat_id = call.message.chat.id
    selected_region = call.data.split(":")[1]
    last_activity[chat_id] = datetime.now()

    user_state[chat_id]['region'] = selected_region

    # Показати список районів
    markup = InlineKeyboardMarkup()
    for district in CLIENTS[selected_region].keys():
        markup.add(InlineKeyboardButton(district, callback_data=f"district:{district}"))
    bot.send_message(chat_id, f"Область {selected_region} вибрана. Оберіть район:", reply_markup=markup)

# Обробка вибору району
@bot.callback_query_handler(func=lambda call: call.data.startswith("district:"))
def handle_district_selection(call):
    chat_id = call.message.chat.id
    selected_district = call.data.split(":")[1]
    last_activity[chat_id] = datetime.now()

    user_state[chat_id]['district'] = selected_district
    selected_region = user_state[chat_id]['region']

    # Показати список клієнтів
    markup = InlineKeyboardMarkup()
    for client in CLIENTS[selected_region][selected_district]:
        markup.add(InlineKeyboardButton(client, callback_data=f"client:{client}"))
    bot.send_message(chat_id, f"Район {selected_district} вибраний. Оберіть клієнта:", reply_markup=markup)

# Обробка вибору клієнта
@bot.callback_query_handler(func=lambda call: call.data.startswith("client:"))
def handle_client_selection(call):
    chat_id = call.message.chat.id
    selected_client = call.data.split(":")[1]
    last_activity[chat_id] = datetime.now()

    user_state[chat_id]['client'] = selected_client
    bot.send_message(chat_id, f"Клієнт {selected_client} вибраний. Тепер завантажте фото.")

# Хендлер для фото
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    chat_id = message.chat.id
    state = user_state.get(chat_id, {})
    last_activity[chat_id] = datetime.now()

    if 'region' not in state or 'district' not in state or 'client' not in state:
        bot.send_message(chat_id, "Спочатку оберіть область, район та клієнта за допомогою кнопки 'Вибрати напрямок'.")
        return

    selected_region = state['region']
    selected_district = state['district']
    selected_client = state['client']

    # Створення папки для області, району та клієнта
    folder_path = os.path.join(BASE_FOLDER, selected_region, selected_district, selected_client)
    os.makedirs(folder_path, exist_ok=True)

    # Завантаження фото
    photo_id = message.photo[-1].file_id
    file_info = bot.get_file(photo_id)
    downloaded_file = bot.download_file(file_info.file_path)

    # Додавання дати і часу до назви файлу
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    photo_name = f"{timestamp}.jpg"
    photo_path = os.path.join(folder_path, photo_name)

    # Збереження фото
    with open(photo_path, 'wb') as photo_file:
        photo_file.write(downloaded_file)

    bot.send_message(chat_id, f"Фото збережено як {photo_name} у папці: {folder_path}")


# # Хендлер для фото
# @bot.message_handler(content_types=['photo'])
# def handle_photo(message):
#     chat_id = message.chat.id
#     last_interaction_time[chat_id] = datetime.now()  # Оновлення часу останньої взаємоді
#     state = user_state.get(chat_id, {})
    
#     if 'user' not in state or 'client' not in state:
#         bot.send_message(chat_id, "Спочатку оберіть користувача та клієнта за допомогою команди /start.")
#         return
    
#     selected_user = state['user']
#     selected_client = state['client']
    
#     # Очищення імен для коректного створення шляхів
#     sanitized_user = sanitize_filename(selected_user)
#     sanitized_client = sanitize_filename(selected_client)
    
#      # Отримуємо ім'я користувача
# username = message.from_user.username or "Без_імені"
# full_name = f"{message.from_user.first_name or ''}_{message.from_user.last_name or ''}".strip().replace(' ', '_')
# user_name_info = username if username else full_name  # Використовуємо username або повне ім'я
   
# #     # Видаляємо недопустимі символи із імені
# safe_user_name = ''.join(c for c in user_name_info if c.isalnum() or c in ('_', '-'))
 

#     # Створення папки для збереження фото
#     folder_path = os.path.join(BASE_FOLDER, sanitized_user, sanitized_client)
#     os.makedirs(folder_path, exist_ok=True)  # Переконайтеся, що папка створена
    
# Хендлер для фото
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    chat_id = message.chat.id
    state = user_state.get(chat_id, {})
    last_activity[chat_id] = datetime.now()

    if 'region' not in state or 'district' not in state or 'client' not in state:
        bot.send_message(chat_id, "Спочатку оберіть область, район та клієнта за допомогою кнопки 'Вибрати напрямок'.")
        return

    selected_region = state['region']
    selected_district = state['district']
    selected_client = state['client']

    # Створення папки для області, району та клієнта
    folder_path = os.path.join(BASE_FOLDER, selected_region, selected_district, selected_client)
    os.makedirs(folder_path, exist_ok=True)


    #      # Отримуємо ім'я користувача
    username = message.from_user.username or "Без_імені"
    full_name = f"{message.from_user.first_name or ''}_{message.from_user.last_name or ''}".strip().replace(' ', '_')
    user_name_info = username if username else full_name  # Використовуємо username або повне ім'я
   
#     # Видаляємо недопустимі символи із імені
    safe_user_name = ''.join(c for c in user_name_info if c.isalnum() or c in ('_', '-'))   

    # Отримання фото
    photo_id = message.photo[-1].file_id
    file_info = bot.get_file(photo_id)
    downloaded_file = bot.download_file(file_info.file_path)
    
      # Додавання дати і імені користувача до назви файлу
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    photo_name = f"{timestamp}_{safe_user_name}.jpg"
    photo_path = os.path.join(folder_path, photo_name)
    
    # Збереження фото
    try:
        with open(photo_path, 'wb') as photo_file:
            photo_file.write(downloaded_file)
        bot.send_message(chat_id, f"Фото збережено як {photo_name} у папці: {folder_path}")
    except Exception as e:
        bot.send_message(chat_id, f"Сталася помилка при збереженні фото: {e}")

def start_polling_with_reconnect():
    while True:
        try:
            print("Запуск бота...")
            bot.polling(none_stop=True)
        except Exception as e:
            print(f"Помилка: {e}")
            print("Втрата підключення. Спроба перепідключення через 5 секунд...")
            time.sleep(5)

# # Запуск бота
# bot.polling()
if __name__ == "__main__":
    start_polling_with_reconnect()