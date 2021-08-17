import psycopg2
from telegram_app.randomari import *


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