import mysql.connector

def create_tables():
    # Подключение к базе данных
    mydb = mysql.connector.connect(
      host="127.0.0.1",
      user="root",
      password="root",
      database="leads"
    )

    # Создание курсора
    mycursor = mydb.cursor()

    # Создание таблицы users
    mycursor.execute("CREATE TABLE IF NOT EXISTS users ("
                     "id INT AUTO_INCREMENT PRIMARY KEY,"
                     "chat_id BIGINT NOT NULL,"
                     "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,"
                     "updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,"
                     "UNIQUE KEY (chat_id)"
                     ")")

    # Создание таблицы chats
    mycursor.execute("CREATE TABLE IF NOT EXISTS chats ("
                     "id INT AUTO_INCREMENT PRIMARY KEY,"
                     "chat_id BIGINT NOT NULL,"
                     "user_id BIGINT NOT NULL,"
                     "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,"
                     "updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,"
                     "FOREIGN KEY (user_id) REFERENCES users(chat_id) ON DELETE CASCADE,"
                     "INDEX(chat_id)"
                     ")")

    # Создание таблицы leads
    mycursor.execute(
        "CREATE TABLE IF NOT EXISTS leads ("
        "id INT AUTO_INCREMENT PRIMARY KEY,"
        "chat_id BIGINT NOT NULL,"
        "chats_id BIGINT NOT NULL,"
        "first_name VARCHAR(255),"
        "last_name VARCHAR(255),"
        "username VARCHAR(255),"
        "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,"
        "updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,"
        "INDEX(chat_id),"
        "FOREIGN KEY (chats_id) REFERENCES chats(chat_id) ON DELETE CASCADE"
        ")"
    )
#Создание таблицы messages
    mycursor.execute(
        "CREATE TABLE IF NOT EXISTS messages ("
        "id INT AUTO_INCREMENT PRIMARY KEY,"
        "chat_id BIGINT ,"
        "chats_id BIGINT ,"
        "message VARCHAR(255),"
        "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,"
        "FOREIGN KEY (chat_id) REFERENCES leads(chat_id) ON DELETE CASCADE"
        ")"
    )
    # Создание таблицы categories
    mycursor.execute(
        "CREATE TABLE IF NOT EXISTS categories ("
        "id INT AUTO_INCREMENT PRIMARY KEY,"
        "category TEXT ,"
        ")"
    )

    # Создание таблицы vocabulary
    mycursor.execute(
        "CREATE TABLE IF NOT EXISTS vocabulary ("
        "id INT AUTO_INCREMENT PRIMARY KEY,"
        "category_id INT ,"
        "word VARCHAR(255) ,"
        "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,"
        "FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE"
        ")"
    )
    # Создание таблицы topics
    mycursor.execute(
        "CREATE TABLE IF NOT EXISTS topics ("
        "id INT AUTO_INCREMENT PRIMARY KEY,"
        "chat_id BIGINT,"
        "chats_id BIGINT,"
        "topic VARCHAR(255),"
        "interest_count INT,"
        "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,"
        "updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,"
        "FOREIGN KEY (chat_id) REFERENCES leads (chat_id) ON DELETE CASCADE"
        ")")

    # Сохранение изменений
    mydb.commit()

    # Закрытие курсора и соединения с базой данных
    mycursor.close()
    mydb.close()