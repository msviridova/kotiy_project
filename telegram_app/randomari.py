import random

import psycopg2
from envparse import Env
from telebot import TeleBot


env = Env()

TOKEN = env.str("TOKEN")
DB_URL = env.str("DB_URL")

SELECT_QUERY = """SELECT * FROM books;"""
INSERT_QUERY = """INSERT INTO books (book_name, author, description, genre, sheets_cnt, added_by) 
VALUES ('%s', '%s', '%s', '%s', %d, '%s');"""
FIND_OBJECT = """ SELECT * FROM books WHERE LOWER(book_name) LIKE LOWER('%%%s%%')"""
FIND_OBJECT_ID = """ SELECT * FROM books WHERE book_id = '%%%d%%'"""


bot = TeleBot(TOKEN)


@bot.message_handler(commands=["ping"])
def echo(message):
    print(f"Получено сообщение из чата {message.chat.id} от {message.from_user.full_name}")


@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, 'Привет, друг! Нашлось свободное время? '
                                      'Чего бы тебе сейчас хотелось - почитать или что-нибудь посмотреть?')


# функция рандомного выбора
@bot.message_handler(commands=['randomize_book'])
def randomize_book(message):
    connect = psycopg2.connect(DB_URL)
    num = random.randint(0, 12)
    with connect.cursor() as cursor:
        cursor.execute(f"""SELECT * FROM books WHERE book_id = '{num}'""")
        res = cursor.fetchone()
    bot.send_message(message.chat.id, f"Самое время почитать '{res[1]}' \n"
                                      f"\n"
                                      f"Автор {res[2]} \n"
                                      f"\n"
                                      f"Описание книги: {res[6]}")


# показать все книги пользователя
@bot.message_handler(commands=["give_my_books"])
def give_my_books(message):
    connect = psycopg2.connect(DB_URL)
    with connect.cursor() as cursor:
        cursor.execute(f"""SELECT * FROM books WHERE added_by LIKE '{message.chat.username}'""")
        res = cursor.fetchall()
    bot.send_message(message.chat.id, str(res))


# добавить книгу (пошагово)
@bot.message_handler(commands=["add_book"])
def name_book(message):
    bot.reply_to(message, text="Введи название книги")
    bot.register_next_step_handler(message, author_book)


def author_book(message):
    name_of_book = message.text
    bot.reply_to(message, text="Введи автора книги (если есть)")
    bot.register_next_step_handler(message, description, name_of_book)


def description(message, name_of_book):
    author_of_book = message.text
    bot.reply_to(message, text="Введи описание книги (если хочется)")
    bot.register_next_step_handler(message, genre_book, name_of_book, author_of_book)


def genre_book(message, name_of_book, author_of_book):
    description_of_book = message.text
    bot.reply_to(message, text="Введи жанр книги")
    bot.register_next_step_handler(message, qnt_sheets, name_of_book, author_of_book, description_of_book)


def qnt_sheets(message, name_of_book, author_of_book, description_of_book):
    genre_of_book = message.text
    bot.reply_to(message, text="Введи количество страниц")
    bot.register_next_step_handler(message, final_step, name_of_book, author_of_book,
                                   description_of_book, genre_of_book)


def final_step(message, name_of_book, author_of_book, description_of_book, genre_of_book):
    sheets_of_book = message.text
    bot.reply_to(message, text=f"Книга: {name_of_book} Автор: {author_of_book} Описание: {description_of_book} "
                               f"Жанр: {genre_of_book} Количество страниц: {sheets_of_book}. "
                               f"Добавляю? да/нет")
    bot.register_next_step_handler(message, committer, name_of_book, author_of_book, description_of_book, genre_of_book,
                                   sheets_of_book)


def committer(message, name_of_book, author_of_book, description_of_book, genre_of_book, sheets_of_book):
    if message.text.lower() == 'да':
        connect = psycopg2.connect(DB_URL)
        with connect.cursor() as cursor:
            cursor.execute(INSERT_QUERY % (name_of_book,
                                           author_of_book,
                                           description_of_book,
                                           genre_of_book,
                                           int(sheets_of_book),
                                           message.chat.username))
            connect.commit()
        bot.reply_to(message, text=f"Записал в базу: Книга: {name_of_book} "
                                   f"Автор: {author_of_book} Описание: {description_of_book} "
                                   f"Жанр: {genre_of_book} Количество страниц: {sheets_of_book}")
    else:
        bot.reply_to(message, text=f"Ладно, ничего записывать не буду")


# поменять данные книги (пошагово)
@bot.message_handler(commands=["change_book"])
def change_book(message):
    data_for_change = message.text[13:]
    connect = psycopg2.connect(DB_URL)
    with connect.cursor() as cursor:
        cursor.execute(FIND_OBJECT % data_for_change)
        results = cursor.fetchall()
        if len(results) > 1:
            for res in results:
                bot.send_message(message.chat.id, f"Я нашел такие данные: \n"
                                                  f"Книга: {res[1]} \n"
                                                  f"\n"
                                                  f"Автор: {res[2]} \n"
                                                  f"\n"
                                                  f"ID этой книги: {res[0]}")
            bot.reply_to(message, text="Какую книгу будем менять? Укажи ID")
            bot.register_next_step_handler(message, choice_results)
        else:
            id_of_book = results[0][0]
            bot.send_message(message.chat.id, f"Я нашел книгу: \n"
                                              f"Книга: '{results[0][1]}' \n"
                                              f"Автор: {results[0][2]}")
            change_results(message, id_of_book)


# если в выдаче больше одного результата, то пользователь указывает id
def choice_results(message):
    id_of_book = message.text
    change_results(message, id_of_book)


# уточнение действия
def change_results(message, id_of_book):
    connect = psycopg2.connect(DB_URL)
    with connect.cursor() as cursor:
        cursor.execute(f""" SELECT * FROM books WHERE book_id = {int(id_of_book)}""")
        result = cursor.fetchone()
    bot.reply_to(message, text=f"Выбрана книга '{result[1]}' автора {result[2]}. \n"
                               f"Что хотелось бы поменять? Введите соответствующую букву и новые данные: \n"
                               f"N - название, \n"
                               f"A - автор, \n"
                               f"D - описание книги, \n"
                               f"G - жанр книги, \n"
                               f"S - количество страниц")
    bot.register_next_step_handler(message, make_the_change, id_of_book)


#выполнение действия
def make_the_change(message, id_of_book):
    if message.text.lower()[0] == 'n':
        new_name = message.text[2:]
        connect = psycopg2.connect(DB_URL)
        with connect.cursor() as cursor:
            cursor.execute(f"UPDATE books SET book_name = CONCAT(UPPER(LEFT('{new_name}', 1)), "
                           f"LOWER(SUBSTRING('{new_name}', 2))) "
                           f"WHERE book_id = {id_of_book}")
            connect.commit()
            bot.reply_to(message, text=f"Изменения применены")
    elif message.text.lower()[0] == 'a':
        new_author = message.text[2:]
        connect = psycopg2.connect(DB_URL)
        with connect.cursor() as cursor:
            cursor.execute(f"UPDATE books SET author = INITCAP('{new_author}') WHERE book_id = {id_of_book}")
            connect.commit()
            bot.reply_to(message, text=f"Изменения применены")
    elif message.text.lower()[0] == 'd':
        new_description = message.text[2:]
        connect = psycopg2.connect(DB_URL)
        with connect.cursor() as cursor:
            cursor.execute(f"UPDATE books SET description = CONCAT(UPPER(LEFT('{new_description}', 1)), "
                           f"SUBSTRING('{new_description}', 2))"
                           f" WHERE book_id = {id_of_book}")
            connect.commit()
            bot.reply_to(message, text=f"Изменения применены")
    elif message.text.lower()[0] == 'g':
        new_genre = message.text[2:]
        connect = psycopg2.connect(DB_URL)
        with connect.cursor() as cursor:
            cursor.execute(f"UPDATE books SET genre = LOWER('{new_genre}')"
                           f" WHERE book_id = {id_of_book}")
            connect.commit()
            bot.reply_to(message, text=f"Изменения применены")
    elif message.text.lower()[0] == 's':
        new_sheets_cnt = message.text[2:]
        connect = psycopg2.connect(DB_URL)
        with connect.cursor() as cursor:
            cursor.execute(f"UPDATE books SET sheets_cnt = {int(new_sheets_cnt)}"
                           f" WHERE book_id = {id_of_book}")
            connect.commit()
            bot.reply_to(message, text=f"Изменения применены")


# удалить книгу (пошагово)
@bot.message_handler(commands=["delete_book"])
def delete_book(message):
    data_for_delete = message.text[13:]
    connect = psycopg2.connect(DB_URL)
    with connect.cursor() as cursor:
        cursor.execute(FIND_OBJECT % data_for_delete)
        results = cursor.fetchall()
        if len(results) > 1:
            for res in results:
                bot.send_message(message.chat.id, f"Найдены такие книги: \n"
                                                  f"Книга: {res[1]} \n"
                                                  f"\n"
                                                  f"Автор: {res[2]} \n"
                                                  f"\n"
                                                  f"ID этой книги: {res[0]}")
            bot.reply_to(message, text="Какую книгу хочешь удалить? Укажи ID")
            bot.register_next_step_handler(message, choice_delete)
        else:
            id_of_book = results[0][0]
            bot.send_message(message.chat.id, f"Найдена книга: \n"
                                              f"Книга: '{results[0][1]}' \n"
                                              f"Автор: {results[0][2]}")
            delete_results(message, id_of_book)


# если в выдаче больше одного результата, то пользователь указывает id
def choice_delete(message):
    id_of_book = message.text
    delete_results(message, id_of_book)


def delete_results(message, id_of_book):
    connect = psycopg2.connect(DB_URL)
    with connect.cursor() as cursor:
        cursor.execute(f""" SELECT * FROM books WHERE book_id = {int(id_of_book)}""")
        result = cursor.fetchone()
    bot.reply_to(message, text=f"Выбрана книга '{result[1]}' автора {result[2]}. \n"
                               f"Удаляем? да/нет")
    bot.register_next_step_handler(message, make_the_delete, id_of_book)


def make_the_delete(message, id_of_book):
    if message.text.lower() == 'да':
        connect = psycopg2.connect(DB_URL)
        with connect.cursor() as cursor:
            cursor.execute(f"DELETE FROM books WHERE book_id = {id_of_book}")
            connect.commit()
            bot.reply_to(message, text=f"Выбранная книга удалена")
    else:
        bot.reply_to(message, text=f"Ладно, оставим все как есть")


bot.polling()
