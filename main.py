import threading
import aiohttp
import telebot
import mysql.connector
from nltk import word_tokenize
import pymorphy3
import nltk
from nltk.corpus import stopwords
from create_tables import create_tables
from telebot import types
import openai

openai.api_key = "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"
# engine = "text-davinci-003"
engine = "gpt-3.5-turbo"

nltk.download('stopwords')
nltk.download('punkt')

bot_id = 6044610942

stop_words = set(stopwords.words('russian'))
stop_words.update('-', ',', '/', '(', ')', '?', '//', '!', '@', '+', '.', ':', ';', '1', '2', '3', '4', '5', '6', '7',
                  '8', '9', '0', 'глаголы', 'существительные')
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


# Класс для анализа чатов с использованием мьютексов
class Analyzer:
    def __init__(self):
        self._chat_id = None
        self._members = []
        self._topic = None
        self.chat_id_lock = threading.Lock()
        self.members_lock = threading.Lock()
        self.topic_lock = threading.Lock()

    def set_chat_id(self, chat_id):
        with self.chat_id_lock:
            self.chat_id = chat_id

    def set_members(self, members):
        with self.members_lock:
            self.members = members

    def set_topic(self, topic):
        with self.topic_lock:
            self.topic = topic


analyzer = Analyzer()


# Обработчик команды /start
@bot.message_handler(commands=['start'], chat_types=['private'])
def send_welcome(message):
    chat_id = message.chat.id
    if chat_id == 555555359:
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
    if message.json['new_chat_participant']['id'] == bot_id:
        chat_id = message.chat.id
        user_id = message.from_user.id
        sql = "INSERT INTO chats (chat_id, user_id) SELECT %s, %s FROM DUAL WHERE NOT EXISTS (SELECT * FROM chats WHERE chat_id = %s AND user_id = %s)"
        val = (chat_id, user_id, chat_id, user_id)
        mycursor.execute(sql, val)
        mydb.commit()
        bot.reply_to(message,
                     "Привет, сладкие попки. Дайте админские права")


@bot.message_handler(func=lambda message: message.text == 'Чаты', chat_types=['private'])
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


@bot.message_handler(func=lambda message: message.text == 'Выбрать чат', chat_types=['private'])
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
        if selected_topic == "Путешествия":
            selected_topic = 'travel'
        elif selected_topic == "Криптовалюта":
            selected_topic = 'crypto'
        elif selected_topic == "IT":
            selected_topic = 'it'
        analyzer.set_topic(selected_topic)
        send_choice_message(call.message.chat.id)
    elif call.data in ['analysis']:
        bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                      reply_markup=None)
        bot.send_message(call.message.chat.id, f"Идёт обработка информации. Ожидайте вывод отчёта")
        lead_generation(call.message.chat.id)
    elif call.data in ['report']:
        bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                      reply_markup=None)
        bot.send_message(call.message.chat.id, f"Идёт обработка информации. Ожидайте вывод отчёта")
        print_report(call.message.chat.id)
    else:
        # Получаем идентификатор выбранного чата из callback_data
        chats_id = int(call.data)
        chat_info = bot.get_chat(chats_id)
        # Создаем новое сообщение с информацией о выбранном чате
        new_message = f"Выбран чат {chat_info.title}"
        # Отправляем новое сообщение в ответ на нажатую кнопку
        bot.send_message(call.message.chat.id, new_message)
        # Удаляем клавиатуру с кнопками
        bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                      reply_markup=None)
        analyzer.set_chat_id(chats_id)
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


def lead_generation(id):
    chats_id = analyzer.chat_id
    # Запрос для поиска первого попавшегося лида с совпадающим chat_id
    select_lead_query = "SELECT chat_id FROM leads WHERE chats_id = %s"
    mycursor.execute(select_lead_query, (chats_id,))
    leads = mycursor.fetchall()
    # Запрос
    prompt = f"Похожие по смыслу глаголы и существительные для темы {analyzer.topic}. Ответ на 1500 символов, в формате перечисления по одному слову, без словосочетаний и выражений"
    # Модель
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": prompt}
        ],
        temperature=0.6,
        max_tokens=1500
    )
    tokens = word_tokenize(completion.choices[0]['message']['content'])
    generated_words = []
    for token in tokens:
        token = token.lower()
        if token not in stop_words:
            generated_words.append(token)
    if analyzer.topic == "crypto":
        add_word_query(generated_words)
    elif analyzer.topic == "IT":

        add_word_query(generated_words)
    elif analyzer.topic == 'travel':
        add_word_query(generated_words)
    mycursor.execute(f"SELECT word FROM {analyzer.topic}")
    words = mycursor.fetchall()

    # Если найден лида с совпадающим chat_id, продолжаем цикл
    for lead in leads:
        for it in lead:
            counter = 0
            # Запрос для получения всех сообщений, связанных с данным лидом
            select_messages_query = "SELECT messages.message FROM messages WHERE chats_id = %s AND chat_id = %s"
            insert_values = (chats_id, it,)
            mycursor.execute(select_messages_query, insert_values)
            messages = mycursor.fetchall()
            messages = preprocess_text(messages)
            for word in words:
                for w in word:
                    for message in messages:
                        if w == message:
                            counter = counter + 1
            query = "SELECT * FROM topics WHERE chat_id = %s AND chats_id = %s AND topic = %s"
            values = (it, analyzer.chat_id, analyzer.topic)
            mycursor.execute(query, values)
            existing_record = mycursor.fetchone()

            if existing_record:
                # Запись существует, выполнение обновления
                update_query = "UPDATE topics SET interest_count = %s, updated_at = NOW() WHERE chat_id = %s AND chats_id = %s"
                update_values = (counter, it, analyzer.chat_id)
                mycursor.execute(update_query, update_values)
                mydb.commit()
            else:
                # Запись не существует, выполнение вставки
                insert_query = "INSERT INTO topics (chat_id, chats_id, topic, interest_count, created_at, updated_at) VALUES (%s, %s, %s, %s, NOW(), NOW())"
                insert_values = (it, analyzer.chat_id, analyzer.topic, counter)
                mycursor.execute(insert_query, insert_values)
                mydb.commit()
    print_report(id)


def add_word_query(words):
    add_word_query = f"INSERT IGNORE INTO {analyzer.topic} (word) VALUES (%s)"
    for word in words:
        mycursor.execute(add_word_query, (word,))
    mydb.commit()


def preprocess_text(text_tuple):
    morph = pymorphy3.MorphAnalyzer()
    lemmas = []
    for text in text_tuple:
        for sent in text:
            if isinstance(sent, str):  # Проверяем, что элемент является строкой
                # Токенизация текста
                tokens = word_tokenize(sent)
                filtered_tokens = []
                # Лемматизация и удаление стоп-слов
                for token in tokens:
                    if token.lower() not in stop_words:
                        filtered_tokens.append(token)
                        parsed_token = morph.parse(token)[0]
                        normal_form = parsed_token.normal_form
                        lemmas.append(normal_form)

    return lemmas


def print_report(chat_id):
    query = "SELECT * from topics WHERE chats_id = %s AND topic = %s"
    values = (analyzer.chat_id, analyzer.topic)
    mycursor.execute(query, values)
    results = mycursor.fetchall()
    message = ""
    if results:
        for result in results:
            query = "SELECT first_name, last_name, username from leads WHERE chats_id = %s AND chat_id = %s"
            values = (analyzer.chat_id, result[1])
            mycursor.execute(query, values)
            responce = mycursor.fetchone()
            name = str(responce[0]) if responce[0] is not None else "Неизвестно"
            surname = str(responce[1]) if responce[1] is not None else "Неизвестно"
            username = str(responce[2]) if responce[2] is not None else "Неизвестно"
            msg = "Имя - " + name + "\n" + "Фамилия - " + surname + "\n" + "Имя пользователя - " + username
            message = str(msg) + "\n" + "Количество заинтересованностей в заданной теме - " + str(result[4])
            bot.send_message(chat_id=chat_id, text=message)
    else:
        bot.send_message(chat_id=chat_id, text="Нет результатов для отчёта")


@bot.message_handler(func=lambda message: message.chat.type == "group" or message.chat.type == "supergroup")
def handle_group_messages(message):
    chat_id = message.from_user.id
    chats_id = message.chat.id
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name
    username = message.from_user.username
    # Проверка наличия лидов с такими же chat_id и chats_id в таблице leads
    check_query = "SELECT * FROM leads WHERE chat_id = %s AND chats_id = %s"
    check_values = (chat_id, chats_id)
    mycursor.execute(check_query, check_values)
    result = mycursor.fetchone()
    if result is None:
        # Запись данных в таблицу leads
        insert_query = "INSERT INTO leads (chat_id, chats_id, first_name, last_name, username) " \
                       "VALUES (%s, %s, %s, %s, %s)"
        insert_values = (chat_id, chats_id, first_name, last_name, username)
        mycursor.execute(insert_query, insert_values)
        mydb.commit()

    # Сохранение сообщения в таблицу messages

    insert_query = "INSERT INTO messages (chat_id, chats_id, message) VALUES (%s, %s, %s)"
    insert_values = (chat_id, chats_id, message.text)
    mycursor.execute(insert_query, insert_values)
    mydb.commit()


# Запуск бота
bot.polling(none_stop=True)
