import threading
from nltk import word_tokenize
import pymorphy3
import nltk
from create_tables import create_tables
from telebot import types
import openai
import config

openai.api_key = config.GPT_API_KEY
engine = config.GPT_ENGINE

nltk.download('stopwords')
nltk.download('punkt')

bot_id = config.BOT_ID

stop_words = config.STOP_WORDS

# Підключення до бази даних
mydb = config.MYSQL

# Створення курсору
mycursor = mydb.cursor()

# Перевірка, чи існують таблиці
mycursor.execute("SHOW TABLES")
tables = mycursor.fetchall()

if not tables:
    # Створення таблиць, якщо вони не існують
    create_tables()

# Створення екземпляра бота
bot = config.TELEGRAM_BOT_API_KEY

# Клас для аналізу чатів
class Analyzer:
    def __init__(self):
        self._chat_id = None
        self._topic = None
        self.chat_id_lock = threading.Lock()
        self.topic_lock = threading.Lock()

    def set_chat_id(self, chat_id):
        with self.chat_id_lock:
            self.chat_id = chat_id

    def set_topic(self, topic):
        with self.topic_lock:
            self.topic = topic

analyzer = Analyzer()

# Обробник команди /start
@bot.message_handler(commands=['start'], chat_types=['private'])
def send_welcome(message):
    chat_id = message.chat.id
    if chat_id == 555555359:
        # Перевіряємо, чи є такий користувач у базі даних
        mycursor.execute("SELECT id FROM users WHERE chat_id = %s", (chat_id,))
        result = mycursor.fetchone()

        if result is None:
            # Якщо такого користувача немає, то реєструємо його
            mycursor.execute("INSERT INTO users (chat_id) VALUES (%s)", (chat_id,))
            mydb.commit()
            bot.send_message(chat_id, "Ви успішно зареєстровані!")
        else:
            bot.send_message(chat_id, "Ви вже зареєстровані у системі!")
        # створюємо клавіатуру
        keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
        # создаем кнопку "Чаты"
        chats_button = types.KeyboardButton('Чати')
        # додаємо кнопку на клавіатуру
        keyboard.add(chats_button)
        # створюємо кнопку "Вибрати чати"
        chats_button = types.KeyboardButton('Вибрати чат')
        # додаємо кнопку на клавіатуру
        keyboard.add(chats_button)
        # надсилаємо повідомлення з використанням клавіатури
        bot.send_message(chat_id,
                         "Будь ласка, додайте мене до потрібного чату, а потім натисніть кнопку Чати, щоб дізнатися чи був доданий бот ",
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
                     "Вітаю. Я аналізуватиму цей текстовий чат. Прошу призначити мене адміністратором")

@bot.message_handler(func=lambda message: message.text == 'Чати', chat_types=['private'])
def show_chats(message):
    user_id = message.chat.id
    mycursor.execute("SELECT chat_id FROM chats WHERE user_id = %s", (user_id,))
    chats = mycursor.fetchall()
    # Створюємо список для назв чатів
    chat_names = []
    # Для кожного чату знаходимо його назву та додаємо його до списку
    for chat in chats:
        try:
            chat_info = bot.get_chat(chat)
            chat_names.append(chat_info.title)
        except:
            pass
    # Якщо список порожній, значить бот не перебуває в жодному чаті
    if not chat_names:
        bot.send_message(message.chat.id, "Бот не доданий в жодний чат.")
    else:
        # Надсилаємо список назв чатів у вигляді тексту
        bot.send_message(message.chat.id, "Список чатів, в яких я перебуваю:\n" + "\n".join(chat_names))

@bot.message_handler(func=lambda message: message.text == 'Вибрати чат', chat_types=['private'])
def select_chat(message):
    user_id = message.chat.id
    mycursor.execute("SELECT chat_id FROM chats WHERE user_id = %s", (user_id,))
    chats = mycursor.fetchall()
    # Створюємо список для назв чатів та їх ідентифікаторів
    chat_names = []
    chat_ids = []
    # Для кожного чату знаходимо його назву та додаємо його до списку
    for chat in chats:
        try:
            chat_info = bot.get_chat(chat)
            chat_names.append(chat_info.title)
            chat_ids.append(chat_info.id)
        except:
            pass

    # Якщо список порожній, значить бот не перебуває в жодному чаті
    if not chat_names:
        bot.send_message(message.chat.id, "Бот не доданий в жодний чат.")
    else:
        # Створюємо клавіатуру
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        # Додаємо кнопки для кожного чату
        for i in range(len(chat_names)):
            callback_data = str(chat_ids[i])
            button = types.InlineKeyboardButton(text=chat_names[i], callback_data=callback_data)
            keyboard.add(button)
        # Надсилаємо повідомлення за допомогою клавіатури
        bot.send_message(message.chat.id, "Будь ласка, виберіть чат:", reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    # Обробляємо натискання кнопки зі списком чатів
    if call.data == 'show_chats':
        show_chats(call.message)
    elif call.data in ['Криптовалюта', 'Подорожі', 'IT']:
        selected_topic = call.data
        # Надсилаємо повідомлення з обраною темою
        bot.send_message(call.message.chat.id, f"Вибрано тему {selected_topic}")
        # Видаляємо клавіатуру з кнопками
        bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                      reply_markup=None)
        if selected_topic == "Подорожі":
            selected_topic = "travel"
        elif selected_topic == "Криптовалюта":
            selected_topic = "crypto"
        elif selected_topic == "IT":
            selected_topic = "it"
        analyzer.set_topic(selected_topic)
        send_choice_message(call.message.chat.id)
    elif call.data in ['analysis']:
        bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                      reply_markup=None)
        bot.send_message(call.message.chat.id, "Обробка інформації. Чекайте на звіт")
        lead_generation(call.message.chat.id)
    elif call.data in ['report']:
        bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                      reply_markup=None)
        bot.send_message(call.message.chat.id, "Обробка інформації. Чекайте на звіт")
        print_report(call.message.chat.id)
    else:
        # Отримуємо ідентифікатор вибраного чату з callback_data
        chats_id = int(call.data)
        chat_info = bot.get_chat(chats_id)
        # Створюємо нове повідомлення з інформацією про обраний чат
        new_message = f"Вибраний чат {chat_info.title}"
        # Надсилаємо нове повідомлення у відповідь на натиснуту кнопку
        bot.send_message(call.message.chat.id, new_message)
        # Видаляємо клавіатуру з кнопками
        bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                      reply_markup=None)
        analyzer.set_chat_id(chats_id)
        send_topic_selection_message(call.message.chat.id)

def send_topic_selection_message(id):
    markup = types.InlineKeyboardMarkup()
    button1 = types.InlineKeyboardButton('Криптовалюта', callback_data='Криптовалюта')
    button2 = types.InlineKeyboardButton('Подорожі', callback_data='Подорожі')
    button3 = types.InlineKeyboardButton('IT', callback_data='IT')
    markup.add(button1, button2, button3)
    bot.send_message(chat_id=id, text='Виберіть тему', reply_markup=markup)

def send_choice_message(id):
    markup = types.InlineKeyboardMarkup()
    button1 = types.InlineKeyboardButton('Аналіз', callback_data='analysis')
    button2 = types.InlineKeyboardButton('Звіт', callback_data='report')
    markup.add(button1, button2)
    bot.send_message(chat_id=id, text='Виберіть наступну дію', reply_markup=markup)

def lead_generation(id):
    chats_id = analyzer.chat_id
    # Запрос для поиска первого попавшегося лида с совпадающим chat_id
    select_lead_query = "SELECT chat_id FROM leads WHERE chats_id = %s"
    mycursor.execute(select_lead_query, (chats_id,))
    leads = mycursor.fetchall()
    # Запрос
    prompt = config.gpt_prompt(analyzer.topic)
    # Модель
    completion = openai.ChatCompletion.create(
        model=engine,
        messages=[
            {"role": "system", "content": prompt}
        ],
        temperature=0.6,
        max_tokens=2500
    )
    tokens = word_tokenize(completion.choices[0]['message']['content'])
    generated_words = []
    for token in tokens:
        token = token.lower()
        if token not in stop_words:
            generated_words.append(token)
    add_word_query(generated_words)
    mycursor.execute(f"SELECT id FROM categories WHERE category = %s", (analyzer.topic, ))
    category_id = mycursor.fetchone()
    mycursor.execute(f"SELECT word FROM vocabulary WHERE category_id = {category_id[0]}")
    words = mycursor.fetchall()

    for lead in leads:
        for it in lead:
            counter = 0
            # Запит на отримання всіх повідомлень, пов'язаних з цим лідом
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
                # Запис існує, виконання оновлення
                update_query = "UPDATE topics SET interest_count = %s, updated_at = NOW() WHERE chat_id = %s AND chats_id = %s"
                update_values = (counter, it, analyzer.chat_id)
                mycursor.execute(update_query, update_values)
                mydb.commit()
            else:
                # Запис не існує, виконання вставки
                insert_query = "INSERT INTO topics (chat_id, chats_id, topic, interest_count, created_at, updated_at) VALUES (%s, %s, %s, %s, NOW(), NOW())"
                insert_values = (it, analyzer.chat_id, analyzer.topic, counter)
                mycursor.execute(insert_query, insert_values)
                mydb.commit()
    print_report(id)

def add_word_query(words):
    query = f"SELECT id FROM categories WHERE category = %s"
    mycursor.execute(query, (analyzer.topic, ))
    category_id = mycursor.fetchone()
    add_word_query = f"INSERT IGNORE INTO vocabulary (word, category_id) VALUES (%s, %s)"
    for word in words:
        mycursor.execute(add_word_query, (word, category_id[0]))
    mydb.commit()

def preprocess_text(text_tuple):
    morph = pymorphy3.MorphAnalyzer()
    lemmas = []
    for text in text_tuple:
        for sent in text:
            if isinstance(sent, str):  # Перевіряємо, що елемент є рядком
                # Токенізація тексту
                tokens = word_tokenize(sent)
                filtered_tokens = []
                # Лематизація та видалення стоп-слів
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
    counter = 0
    if results:
        for result in results:
            if result[4] > config.INTERESTS:
                query = "SELECT first_name, last_name, username from leads WHERE chats_id = %s AND chat_id = %s"
                values = (analyzer.chat_id, result[1])
                mycursor.execute(query, values)
                responce = mycursor.fetchone()
                name = str(responce[0]) if responce[0] is not None else "Невідомо"
                surname = str(responce[1]) if responce[1] is not None else "Невідомо"
                username = "@" + str(responce[2]) if responce[2] is not None else "Невідомо"
                msg = "Ім'я - " + name + "\n" + "Прізвище - " + surname + "\n" + "Ім'я користувача - " + username
                message = str(msg) + "\n" + "Кількість зацікавлень у заданій темі - " + str(result[4])
                bot.send_message(chat_id=chat_id, text=message)
                counter+=1
        if counter == 0:
            bot.send_message(chat_id=chat_id, text="У цьому чаті дуже мало згадок про задану тему")
    else:
        bot.send_message(chat_id=chat_id, text="Немає результатів для звіту")

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
        # Запис даних у таблицю leads
        insert_query = "INSERT INTO leads (chat_id, chats_id, first_name, last_name, username) " \
                       "VALUES (%s, %s, %s, %s, %s)"
        insert_values = (chat_id, chats_id, first_name, last_name, username)
        mycursor.execute(insert_query, insert_values)
        mydb.commit()

    # Збереження повідомлення до таблиці messages

    insert_query = "INSERT INTO messages (chat_id, chats_id, message) VALUES (%s, %s, %s)"
    insert_values = (chat_id, chats_id, message.text)
    mycursor.execute(insert_query, insert_values)
    mydb.commit()

# Запуск бота
bot.polling(none_stop=True)
