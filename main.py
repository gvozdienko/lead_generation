import telebot
import mysql.connector
from create_tables import create_tables
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from telebot import types

# Подключение к базе данных
mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    password="root",
    database="leads"
)

# Создание курсора
mycursor = mydb.cursor()

# Проверка, существуют ли таблицы
mycursor.execute("SHOW TABLES")
tables = mycursor.fetchall()

if not tables:
    # Создание таблиц, если они не существуют
    create_tables()

# Создание экземпляра бота
bot = telebot.TeleBot("6044610942:AAFSAakXSNxj4L5RDSFKy5_dmKqEg8dogQk")


# Обработчик команды /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id

    # Проверяем, есть ли такой пользователь в базе данных
    mycursor.execute("SELECT id FROM users WHERE chat_id = %s", (chat_id,))
    result = mycursor.fetchone()

    if result is None:
        # Если такого пользователя нет, то регистрируем его
        mycursor.execute("INSERT INTO users (chat_id) VALUES (%s)", (chat_id,))
        mydb.commit()
        bot.send_message(chat_id, "Вы успешно зарегистрированы!")
    else:
        bot.send_message(chat_id, "Вы уже зарегистрированы в системе!")
        # создаем клавиатуру
        keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
        # создаем кнопку "Чаты"
        chats_button = types.KeyboardButton('Чаты')
        # добавляем кнопку на клавиатуру
        keyboard.add(chats_button)
        # создаем кнопку "Выбрать аты"
        chats_button = types.KeyboardButton('Выбрать чат')
        # добавляем кнопку на клавиатуру
        keyboard.add(chats_button)
        # отправляем сообщение с использованием клавиатуры
        bot.send_message(chat_id,
                         "Пожалуйста, добавьте меня в нужный чат, а затем нажмите кнопку Чаты, чтобы узнать был ли добавлен бот ",
                         reply_markup=keyboard)


@bot.message_handler(content_types=['new_chat_members'])
def on_new_chat_member(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    sql = "INSERT INTO chats (chat_id, user_id) SELECT %s, %s FROM DUAL WHERE NOT EXISTS (SELECT * FROM chats WHERE chat_id = %s AND user_id = %s)"
    val = (chat_id, user_id, chat_id, user_id)
    mycursor.execute(sql, val)
    mydb.commit()
    bot.reply_to(message,
                 "Спасибо, что добавили меня в этот чат! Я буду записывать информацию о чатах, в которых я нахожусь.")


@bot.message_handler(func=lambda message: message.text == 'Чаты')
def show_chats(message):
    user_id = message.chat.id
    mycursor.execute("SELECT chat_id FROM chats WHERE user_id = %s", (user_id,))
    chats = mycursor.fetchall()

    # Создаем список для названий чатов
    chat_names = []

    # Для каждого чата находим его название и добавляем его в список
    for chat in chats:
        try:
            chat_info = bot.get_chat(chat)
            chat_names.append(chat_info.title)
        except:
            pass

    # Если список пустой, значит бот не состоит ни в одном чате
    if not chat_names:
        bot.send_message(message.chat.id, "Бот не состоит ни в одном чате.")
    else:
        # Отправляем список названий чатов в виде текста
        bot.send_message(message.chat.id, "Список чатов, в которых я состою:\n\n" + "\n".join(chat_names))


@bot.message_handler(func=lambda message: message.text == 'Выбрать чат')
def select_chat(message):
    user_id = message.chat.id
    mycursor.execute("SELECT chat_id FROM chats WHERE user_id = %s", (user_id,))
    chats = mycursor.fetchall()

    # Создаем список для названий чатов и их идентификаторов
    chat_names = []
    chat_ids = []

    # Для каждого чата находим его название и добавляем его в список
    for chat in chats:
        try:
            chat_info = bot.get_chat(chat)
            chat_names.append(chat_info.title)
            chat_ids.append(chat_info.id)
        except:
            pass

    # Если список пустой, значит бот не состоит ни в одном чате
    if not chat_names:
        bot.send_message(message.chat.id, "Бот не состоит ни в одном чате.")
    else:
        # Создаем клавиатуру
        keyboard = types.InlineKeyboardMarkup(row_width=1)

        # Добавляем кнопки для каждого чата
        for i in range(len(chat_names)):
            callback_data = str(chat_ids[i])
            button = types.InlineKeyboardButton(text=chat_names[i], callback_data=callback_data)
            keyboard.add(button)

        # Отправляем сообщение с использованием клавиатуры
        bot.send_message(message.chat.id, "Пожалуйста, выберите чат:", reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    # Обрабатываем нажатие кнопки со списком чатов
    if call.data == 'show_chats':
        show_chats(call.message)
    elif call.data in ['Криптовалюта', 'Путешествия', 'IT']:
        selected_topic = call.data
        # Отправляем сообщение с выбранной темой
        bot.send_message(call.message.chat.id, f"Выбрана тема {selected_topic}")
        # Удаляем клавиатуру с кнопками
        bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                      reply_markup=None)
        send_choice_message(call.message.chat.id)
    elif call.data in ['analysis', 'report']:
        bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                      reply_markup=None)
    else:
        # Получаем идентификатор выбранного чата из callback_data
        chat_id = int(call.data)
        chat_info = bot.get_chat(chat_id)
        # Создаем новое сообщение с информацией о выбранном чате
        new_message = f"Выбран чат {chat_info.title}"
        # Отправляем новое сообщение в ответ на нажатую кнопку
        bot.send_message(call.message.chat.id, new_message)
        # Удаляем клавиатуру с кнопками
        bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                      reply_markup=None)
        send_topic_selection_message(call.message.chat.id)


def send_topic_selection_message(id):

    markup = types.InlineKeyboardMarkup()
    button1 = types.InlineKeyboardButton('Криптовалюта', callback_data='Криптовалюта')
    button2 = types.InlineKeyboardButton('Путешествия', callback_data='Путешествия')
    button3 = types.InlineKeyboardButton('IT', callback_data='IT')
    markup.add(button1, button2, button3)
    bot.send_message(chat_id=id, text='Выберите тему', reply_markup=markup)


def send_choice_message(id):
    markup = types.InlineKeyboardMarkup()
    button1 = types.InlineKeyboardButton('Анализ', callback_data='analysis')
    button2 = types.InlineKeyboardButton('Отчёт', callback_data='report')
    markup.add(button1, button2)
    bot.send_message(chat_id=id, text='Выберите следущее действие', reply_markup=markup)

# Запуск бота
bot.polling(none_stop=True)
