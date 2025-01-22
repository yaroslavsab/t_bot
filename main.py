import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, InputMediaPhoto, InputMediaVideo
import os
import pandas as pd
import re
from telebot import apihelper, types  
import time 
from datetime import datetime, timedelta
import threading
import math

# Налаштування таймауту для всіх запитів
apihelper.CONNECT_TIMEOUT = 30  # Таймаут підключення
apihelper.READ_TIMEOUT = 30     # Таймаут читання відповіді

# Токен  бота
API_TOKEN = '7602893334:AAFMYoVxfDxgeQjmX68RX7Ri_4gGFMe2wlk'
bot = telebot.TeleBot(API_TOKEN, parse_mode=None)



def clean_folder_name(name):
  #  """Функція для очищення імені папки"""
    name = re.sub(r'[^\w\s]', '', name)  # Видалення некоректних символів
    name = re.sub(r'\s+', ' ', name).strip()  # Заміна множинних пробілів на один
    return name

# Функція для очищення імен
def sanitize_filename(name):
    # Видаляємо заборонені символи та зайві пробіли
    name = re.sub(r'[<>:"/\\|?*,]', '_', name)  # Заміняємо недопустимі символи
    return name.strip()  # Видаляємо зайві пробіли

# Завантажуємо користувачів і клієнтів з Excel
# USERS = load_clients_from_excel('clients.xls')  # Замість 'clients.xlsx' вкажіть свій шлях до файлу Excel

# Дані з Excel
EXCEL_FILE = r'E:\bot\clients.xls'  # Шлях до вашого файлу Excel

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
BASE_FOLDER = 'E:\\bot\\user_client_photos'
os.makedirs(BASE_FOLDER, exist_ok=True)

# Стан для кожного користувача
user_state = {}
last_interaction_time = {}  # Відстеження останньої взаємодії з ботом
last_activity = {}
INACTIVITY_LIMIT = timedelta(hours=1)  # Часовий ліміт бездіяльності

# # Функція перевірки активності
# def check_inactivity():
#     while True:
#         now = datetime.now()
#         for chat_id in list(last_interaction_time.keys()):
#             if now - last_interaction_time[chat_id] > INACTIVITY_LIMIT:
#                 del last_interaction_time[chat_id]  # Видалення користувача після закінчення часу
#                 if chat_id in user_state:
#                     del user_state[chat_id]
#                 try:
#                     bot.send_message(chat_id, "Час бездіяльності завершено. Натисніть /start, щоб почати заново.")
#                 except Exception as e:
#                     print(f"Помилка надсилання повідомлення: {e}")
#         threading.Event().wait(60)  # Перевірка кожну хвилину

# # Запуск перевірки бездіяльності у фоновому потоці
# threading.Thread(target=check_inactivity, daemon=True).start()

# Функція для очищення історії і показу кнопки
def reset_user(chat_id):
    user_state.pop(chat_id, None)  # Очистити стан
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("Вибрати напрямок"))
#    bot.send_message(chat_id, "Час бездіяльності закінчився. Натисніть 'Вибрати напрямок' для продовження.", reply_markup=markup)

# Функція для перевірки бездіяльності
def check_inactivity():
    while True:
        now = datetime.now()
        for chat_id in list(last_activity.keys()):
            if now - last_activity[chat_id] > INACTIVITY_LIMIT:
                reset_user(chat_id)
                last_activity.pop(chat_id, None)  # Видалити запис про активність
        time.sleep(60)  # Перевіряти кожну хвилину

# Запустити перевірку бездіяльності в окремому потоці

threading.Thread(target=check_inactivity, daemon=True).start()

# Функція для санітизації callback_data
def sanitize_callback_data(data):
    return data[:64]  # Обрізаємо до 64 символів


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
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("Вибрати напрямок"))
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

    # # Показати список клієнтів
    # markup = InlineKeyboardMarkup()
    # for client in CLIENTS[selected_region][selected_district]:
    #     markup.add(InlineKeyboardButton(client, callback_data=f"client:{client}"))
    # bot.send_message(chat_id, f"Район {selected_district} вибраний. Оберіть клієнта:", reply_markup=markup)

 # Показати першу сторінку клієнтів
    clients = CLIENTS[selected_region][selected_district]
    user_state[chat_id]['clients'] = clients  # Зберігаємо список клієнтів
    user_state[chat_id]['page'] = 0  # Початкова сторінка
    show_clients_page(chat_id, clients, 0)

# Функція для відображення клієнтів на певній сторінці
def show_clients_page(chat_id, clients, page):
    items_per_page = 15  # Кількість клієнтів на одній сторінці
    start = page * items_per_page
    end = start + items_per_page
    clients_page = clients[start:end]

    markup = InlineKeyboardMarkup()
    for client in clients_page:
        markup.add(InlineKeyboardButton(client, callback_data=f"client:{client}"))

    # Додавання кнопок навігації
    if page > 0:
        markup.add(InlineKeyboardButton("⬅️ Попередня", callback_data=f"page:{page - 1}"))
    if end < len(clients):
        markup.add(InlineKeyboardButton("➡️ Наступна", callback_data=f"page:{page + 1}"))

    bot.send_message(chat_id, f"Список клієнтів (сторінка {page + 1}):", reply_markup=markup)

# Обробка зміни сторінки
@bot.callback_query_handler(func=lambda call: call.data.startswith("page:"))
def handle_page_change(call):
    chat_id = call.message.chat.id
    page = int(call.data.split(":")[1])
    last_activity[chat_id] = datetime.now()

    clients = user_state[chat_id].get('clients')
    if clients is not None:
        user_state[chat_id]['page'] = page
        # bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id,
        #                       text=f"Список клієнтів (сторінка {page + 1}):")
        show_clients_page(chat_id, clients, page)
    else:
        bot.answer_callback_query(call.id, "Помилка: список клієнтів не знайдено.")

# Обробка вибору клієнта
@bot.callback_query_handler(func=lambda call: call.data.startswith("client:"))
def handle_client_selection(call):
    chat_id = call.message.chat.id
    selected_client = call.data.split(":")[1]
    last_activity[chat_id] = datetime.now()

    bot.send_message(chat_id, f"Клієнт {selected_client} вибраний. Тепер завантажте фото або відео.")


# # Обробка вибору клієнта
# @bot.callback_query_handler(func=lambda call: call.data.startswith("client:"))
# def handle_client_selection(call):
#     chat_id = call.message.chat.id
#     selected_client = call.data.split(":")[1]
#     last_activity[chat_id] = datetime.now()

#     user_state[chat_id]['client'] = selected_client
#     bot.send_message(chat_id, f"Клієнт {selected_client} вибраний. Тепер завантажте фото або відео.")


# # Обробка вибору клієнта з пагінацією
# @bot.callback_query_handler(func=lambda call: call.data.startswith("client:"))
# def handle_client_selection(call):
#     data = call.data.split(":")
#     chat_id = call.message.chat.id
#     if len(data) == 3 and data[1] == "prev" or data[1] == "next":
#         # Пагінація
#         district = data[2]
#         page = int(data[3])
#         keyboard = create_paginated_keyboard(clients[district], page, f"client:{district}")
#         bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=keyboard)
#     else:
#         # Вибір клієнта
#         selected_client = data[1]
#         bot.send_message(call.message.chat.id, f"Ви обрали клієнта: {selected_client}")



@bot.message_handler(content_types=['photo', 'media_group'])
def handle_media_group(message):
    chat_id = message.chat.id
    state = user_state.get(chat_id, {})

    # Перевіряємо, чи обрані напрямок, район і клієнт
    if 'region' not in state or 'district' not in state or 'client' not in state:
        bot.send_message(chat_id, "Спочатку оберіть напрямок, район і клієнта за допомогою кнопки 'Вибрати напрямок'.")
        return

    region = state['region']
    district = state['district']
    client = state['client']

    # Створення папки для збереження фото
    folder_path = os.path.join(BASE_FOLDER, region, district, client)
    os.makedirs(folder_path, exist_ok=True)

    def generate_unique_filename(folder, base_name, extension):
        """Генерує унікальне ім'я файлу, якщо файл уже існує."""
        counter = 1
        file_name = f"{base_name}{extension}"
        while os.path.exists(os.path.join(folder, file_name)):
            file_name = f"{base_name}_{counter}{extension}"
            counter += 1
        return file_name

    # Обробка фото чи альбому
    if message.content_type == 'media_group':
        # Альбом фото
        if len(message.photo) > 5:
            bot.send_message(chat_id, "Можна завантажити не більше 5 фото за один раз.")
            return

        for index, media in enumerate(message.photo):
            try:
                photo_id = media.file_id
                file_info = bot.get_file(photo_id)
                downloaded_file = bot.download_file(file_info.file_path)

                # Формуємо назву файлу
                timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                base_name = f"{timestamp}_{index + 1}"
                unique_name = generate_unique_filename(folder_path, base_name, ".jpg")
                photo_path = os.path.join(folder_path, unique_name)

                # Зберігаємо файл
                with open(photo_path, 'wb') as photo_file:
                    photo_file.write(downloaded_file)

                bot.send_message(chat_id, f"Фото {index + 1} збережено як {unique_name}.")
            except Exception as e:
                bot.send_message(chat_id, f"Помилка під час збереження фото: {str(e)}")
    elif message.content_type == 'photo':
        # Одне фото
        try:
            photo_id = message.photo[-1].file_id
            file_info = bot.get_file(photo_id)
            downloaded_file = bot.download_file(file_info.file_path)

            # Формуємо назву файлу
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            base_name = f"{timestamp}_single"
            unique_name = generate_unique_filename(folder_path, base_name, ".jpg")
            photo_path = os.path.join(folder_path, unique_name)

            # Зберігаємо файл
            with open(photo_path, 'wb') as photo_file:
                photo_file.write(downloaded_file)

            bot.send_message(chat_id, f"Фото збережено як {unique_name}.")
        except Exception as e:
            bot.send_message(chat_id, f"Помилка під час збереження фото: {str(e)}")



# @bot.message_handler(content_types=['photo', 'media_group'])
# def handle_media_group(message):
#     chat_id = message.chat.id
#     state = user_state.get(chat_id, {})

#     # Перевіряємо, чи обрані напрямок, район і клієнт
#     if 'region' not in state or 'district' not in state or 'client' not in state:
#         bot.send_message(chat_id, "Спочатку оберіть напрямок, район і клієнта за допомогою кнопки 'Вибрати напрямок'.")
#         return

#     region = state['region']
#     district = state['district']
#     client = state['client']

#     # Створення папки для збереження фото
#     folder_path = os.path.join(BASE_FOLDER, region, district, client)
#     os.makedirs(folder_path, exist_ok=True)

#     # Обробка фото чи альбому
#     if message.content_type == 'media_group':
#         # Альбом фото
#         if len(message.photo) > 5:
#             bot.send_message(chat_id, "Можна завантажити не більше 5 фото за один альбом.")
#             return

#         for index, media in enumerate(message.photo):
#             try:
#                 photo_id = media.file_id
#                 file_info = bot.get_file(photo_id)
#                 downloaded_file = bot.download_file(file_info.file_path)

#                 # Формуємо унікальну назву файлу
#                 timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
#                 photo_name = f"{timestamp}_{index + 1}.jpg"
#                 photo_path = os.path.join(folder_path, photo_name)

#                 # Зберігаємо файл
#                 with open(photo_path, 'wb') as photo_file:
#                     photo_file.write(downloaded_file)
                
#                 bot.send_message(chat_id, f"Фото {index + 1} збережено як {photo_name}.")
#             except Exception as e:
#                 bot.send_message(chat_id, f"Помилка під час збереження фото: {str(e)}")
#     elif message.content_type == 'photo':
#         # Одне фото
#         try:
#             photo_id = message.photo[-1].file_id
#             file_info = bot.get_file(photo_id)
#             downloaded_file = bot.download_file(file_info.file_path)

#             # Формуємо унікальну назву файлу
#             timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
#             photo_name = f"{timestamp}_single.jpg"
#             photo_path = os.path.join(folder_path, photo_name)

#             # Зберігаємо файл
#             with open(photo_path, 'wb') as photo_file:
#                 photo_file.write(downloaded_file)

#             bot.send_message(chat_id, f"Фото збережено як {photo_name}.")
#         except Exception as e:
#             bot.send_message(chat_id, f"Помилка під час збереження фото: {str(e)}")


# # Хендлер для фото
# @bot.message_handler(content_types=['photo'])
# def handle_photo(message):
#     chat_id = message.chat.id
#     state = user_state.get(chat_id, {})
#     last_activity[chat_id] = datetime.now()

#     if 'region' not in state or 'district' not in state or 'client' not in state:
#         bot.send_message(chat_id, "Спочатку оберіть область, район та клієнта за допомогою кнопки 'Вибрати напрямок'.")
#         return

#     selected_region = state['region']
#     selected_district = state['district']
#     selected_client = state['client']

#     # Створення папки для області, району та клієнта
#     folder_path = os.path.join(BASE_FOLDER, selected_region, selected_district, selected_client)
#     os.makedirs(folder_path, exist_ok=True)

#     # Завантаження фото
#     photo_id = message.photo[-1].file_id
#     file_info = bot.get_file(photo_id)
#     downloaded_file = bot.download_file(file_info.file_path)

#     # Додавання дати і часу до назви файлу
#     timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
#     photo_name = f"{timestamp}.jpg"
#     photo_path = os.path.join(folder_path, photo_name)

#     # Збереження фото
#     with open(photo_path, 'wb') as photo_file:
#         photo_file.write(downloaded_file)

#     bot.send_message(chat_id, f"Фото збережено як {photo_name} у папці: {folder_path}")

    
# # Хендлер для фото
# @bot.message_handler(content_types=['photo'])
# def handle_photo(message):
#     chat_id = message.chat.id
#     state = user_state.get(chat_id, {})
#     last_activity[chat_id] = datetime.now()

#     if 'region' not in state or 'district' not in state or 'client' not in state:
#         bot.send_message(chat_id, "Спочатку оберіть область, район та клієнта за допомогою кнопки 'Вибрати напрямок'.")
#         return
   
#     # Створення папки для користувача, клієнта та регіону
#     region = clean_folder_name(user_state[chat_id]['region'])
#     district = clean_folder_name(user_state[chat_id]['district'])
#     client = clean_folder_name(user_state[chat_id]['client'])

#     folder_path = os.path.join(BASE_FOLDER, region, district, client)
#     os.makedirs(folder_path, exist_ok=True)



#     #      # Отримуємо ім'я користувача
#     username = message.from_user.username or "Без_імені"
#     full_name = f"{message.from_user.first_name or ''}_{message.from_user.last_name or ''}".strip().replace(' ', '_')
#     user_name_info = username if username else full_name  # Використовуємо username або повне ім'я
   
# #     # Видаляємо недопустимі символи із імені
#     safe_user_name = ''.join(c for c in user_name_info if c.isalnum() or c in ('_', '-'))   

#     # Отримання фото
#     photo_id = message.photo[-1].file_id
#     file_info = bot.get_file(photo_id)
#     downloaded_file = bot.download_file(file_info.file_path)
    
#       # Додавання дати і імені користувача до назви файлу
#     timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
#     photo_name = f"{timestamp}_{safe_user_name}.jpg"
#     photo_path = os.path.join(folder_path, photo_name)
    
#     # Збереження фото
#     try:
#         with open(photo_path, 'wb') as photo_file:
#             photo_file.write(downloaded_file)
#         bot.send_message(chat_id, f"Фото збережено як {photo_name} у папці: {folder_path}")
#     except Exception as e:
#         bot.send_message(chat_id, f"Сталася помилка при збереженні фото: {e}")

# Хендлер для отримання відео
@bot.message_handler(content_types=['video'])
def handle_video(message):
    chat_id = message.chat.id
    state = user_state.get(chat_id, {})
    
    # Перевіряємо, чи обрані напрямок, район та клієнт
    if 'region' not in state or 'district' not in state or 'client' not in state:
        bot.send_message(chat_id, "Спочатку оберіть напрямок, район і клієнта за допомогою кнопки 'Вибрати напрямок'.")
        return

    region = state['region']
    district = state['district']
    client = state['client']
    
    # Створення папки для збереження відео
    folder_path = os.path.join(BASE_FOLDER, region, district, client)
    os.makedirs(folder_path, exist_ok=True)
    
    # Отримуємо інформацію про файл
    video_id = message.video.file_id
    file_info = bot.get_file(video_id)
    downloaded_file = bot.download_file(file_info.file_path)

    # Формуємо назву файлу
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    video_name = f"{timestamp}.mp4"
    video_path = os.path.join(folder_path, video_name)

    # Збереження відео
    with open(video_path, 'wb') as video_file:
        video_file.write(downloaded_file)

    # Відправляємо повідомлення про успішне збереження
    bot.send_message(chat_id, f"Відео збережено як {video_name} у папку: {folder_path}")

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