import telebot
from telebot import types
import configparser
from mailto import mailto
import hashlib
from __extra import TMDB, RequestServer
from urllib3.exceptions import ReadTimeoutError
from requests.exceptions import ReadTimeout
from smtplib import SMTPDataError
import time
from telebot import apihelper

config = configparser.ConfigParser()
config.read("settings.ini")

top10 = {"data": None, "len": None, "current": 0}

apihelper.proxy = {
    'https': "socks5://14611055481:U777Vluhz8@orbtl.s5.opennetwork.cc:999"
}
bot = telebot.TeleBot(config["BOT"]["token"])


def generate_code(chat_id):
    key = hashlib.md5(bytes(chat_id))
    return str(key.hexdigest())[:12]


@bot.message_handler(commands=["start"])
def repeat_all_messages(message):
    try:
        exist = server_api.check_existing(message.chat.id)["boolean"]
        if not exist:
            server_api.create_new(message.chat.id)
            bot.send_sticker(message.chat.id, config["STICKER"]["hello"])
            bot.send_message(message.chat.id,
                             "Привет, тебе нужно зарегистрироваться прежде, чем начать!\nДля регистрации "
                             "используй /register")
        else:
            bot.send_message(message.chat.id, "Я уже давно знаю тебя :)")
            bot.send_message(message.chat.id, "Используй /reset, чтобы стереть данные")
    except (TypeError, KeyError):
        bot.send_sticker(message.chat.id, config["STICKER"]["tired"])
        bot.send_message(message.chat.id, "Извините, бот сейчас устал и не может работать!")


@bot.message_handler(commands=["help"])
def repeat_all_messages(message):
    try:
        exist = server_api.check_existing(message.chat.id)["boolean"]
        if exist:
            current = server_api.get_user(message.chat.id)
            if current["hash"] != -1:
                bot.reply_to(message, "Используй:\n1) /top10\n2) /random\n3) Найти <название> (только EN)")
            else:
                bot.send_sticker(message.chat.id, config["STICKER"]["angry"])
                if current["state"] == 0:
                    bot.send_message(message.chat.id, "Ты еще не зарегистрировался!!!\nИспользуй /register")
                else:
                    bot.send_message(message.chat.id, "Подтверди свою почту!")
        else:
            bot.send_message(message.chat.id, "Ты еще не зарегистрировался!!!\nИспользуй /register")
    except TypeError:
        bot.send_sticker(message.chat.id, config["STICKER"]["tired"])
        bot.send_message(message.chat.id, "Извините, бот сейчас устал и не может работать!")


@bot.message_handler(commands=["register"])
def register(message):
    try:
        exist = server_api.check_existing(message.chat.id)["boolean"]
        if not exist:
            server_api.create_new(message.chat.id)
        res = server_api.change_state(message.chat.id, 1)
        if res["status_code"] != 501:
            bot.send_message(message.chat.id,
                             "Напиши свою существующую Почту, туда я отправлю код подтверждения\nКод скиньте мне в чат!")
            bot.send_message(message.chat.id, "Для удаления данных используй /reset")
        else:
            bot.send_sticker(message.chat.id, config["STICKER"]["furious"])
            bot.send_message(message.chat.id, "Упс... /reset и давайте познакомимся с вами снова!")
    except TypeError as e:
        bot.send_sticker(message.chat.id, config["STICKER"]["tired"])
        bot.send_message(message.chat.id, "Извините, бот сейчас устал и не может работать!")


@bot.message_handler(commands=["reset"])
def reset_state(message):
    try:
        res = server_api.delete_user(message.chat.id)
        if res["status_code"] != 501:
            bot.send_sticker(message.chat.id, config["STICKER"]["deleted"])
            bot.send_message(message.chat.id, "Данные успешно удалены")
        else:
            bot.send_sticker(message.chat.id, config["STICKER"]["furious"])
            bot.send_message(message.chat.id, "У меня нету твоих данных")
    except TypeError:
        bot.send_sticker(message.chat.id, config["STICKER"]["tired"])
        bot.send_message(message.chat.id, "Извините, бот сейчас устал и не может работать!")


@bot.message_handler(commands=["random"])
def random(message):
    try:
        global top10
        exist = server_api.check_existing(message.chat.id)["boolean"]
        if not exist:
            bot.send_message(message.chat.id, "Используй /start")
        else:
            current = server_api.get_user(message.chat.id)
            if current["state"] != 3:
                bot.send_message("Пройдите аунтификацию. /register")
            else:
                bot.send_message(message.chat.id, "Подожди немного, пока я собираю данные :)")
                top10["data"] = filmapi.ten_random_films()
                top10["len"] = len(top10["data"])
                markup = types.InlineKeyboardMarkup(row_width=2)
                item1 = types.InlineKeyboardButton("⬅", callback_data='Prev')
                item2 = types.InlineKeyboardButton("➡", callback_data='Next')
                error = True
                # noinspection PyBroadException
                while error:
                    try:
                        url = server_api.open_full(top10["data"][top10["current"]])
                        error = False
                    except Exception as e:
                        print(e)
                if url is not None:
                    item3 = types.InlineKeyboardButton("Открыть в браузере", url=url)
                    markup.add(item1, item2, item3)
                else:
                    markup.add(item1, item2)
                bot.send_photo(message.chat.id, photo=top10["data"][top10["current"]]["poster"],
                               caption=f'<b>{top10["data"][top10["current"]]["title"]}</b>\n\n'
                                       f'{top10["data"][top10["current"]]["description"]}\n\n'
                                       f'Rate: {top10["data"][top10["current"]]["vote_average"]}',
                               parse_mode="html", reply_markup=markup)
    except TypeError:
        bot.send_sticker(message.chat.id, config["STICKER"]["tired"])
        bot.send_message(message.chat.id, "Извините, бот сейчас устал и не может работать!")


@bot.message_handler(commands=["top10"])
def top(message):
    try:
        global top10
        exist = server_api.check_existing(message.chat.id)["boolean"]
        if not exist:
            bot.send_message(message.chat.id, "Используй /start")
        else:
            current = server_api.get_user(message.chat.id)
            if current["state"] != 3:
                bot.send_message("Пройдите аунтификацию. /register")
            else:
                bot.send_message(message.chat.id, "Подожди немного, пока я собираю данные :)")
                top10["data"] = filmapi.popular_films()
                top10["len"] = len(top10["data"])
                markup = types.InlineKeyboardMarkup(row_width=2)
                item1 = types.InlineKeyboardButton("⬅", callback_data='Prev')
                item2 = types.InlineKeyboardButton("➡", callback_data='Next')
                url = server_api.open_full(top10["data"][top10["current"]])
                if url is not None:
                    item3 = types.InlineKeyboardButton("Открыть в браузере", url=url)
                    markup.add(item1, item2, item3)
                else:
                    markup.add(item1, item2)
                bot.send_photo(message.chat.id, photo=top10["data"][top10["current"]]["poster"],
                               caption=f'<b>{top10["data"][top10["current"]]["title"]}</b>\n\n'
                                       f'{top10["data"][top10["current"]]["description"]}\n\n'
                                       f'Rate: {top10["data"][top10["current"]]["vote_average"]}',
                               parse_mode="html", reply_markup=markup)
    except TypeError:
        bot.send_sticker(message.chat.id, config["STICKER"]["tired"])
        bot.send_message(message.chat.id, "Извините, бот сейчас устал и не может работать!")


@bot.message_handler(content_types=['text'])
def answer(message):
    try:
        exist = server_api.check_existing(message.chat.id)["boolean"]
        if exist:
            current = server_api.get_user(message.chat.id)
            if current["state"] == 1:
                login, email = generate_code(message.chat.id) + "12121212", message.text
                hash = generate_code(message.chat.id)
                res = server_api.change_some_fields(message.chat.id,
                                                    {"state": 2, "hash": hash, "login": login, "email": email})
                if res["status_code"] == 200:
                    bot.send_message(message.chat.id, "Спасибо за регистрацию, проверьте почту!")
                    try:
                        post = mailto.Request(config["MAIL"]['login'], config["MAIL"]['password'])
                        post.send_email('The request to sign in FilmLineBot', email,
                                        f"The auth code - {hash}\nThis is the password to sign up, do not lose it!")
                        post.server.close()
                    except (ConnectionAbortedError, ConnectionError, ReadTimeout, ReadTimeoutError, SMTPDataError):
                        bot.send_message(message.chat.id,
                                         f"Ваша почта считает, что я СПАМ, так что вот, не теряйте - {hash}")
                        post.server.close()
                else:
                    bot.send_sticker(message.chat.id, config["STICKER"]["furious"])
                    bot.send_message(message.chat.id, "Упс... /reset (Оказывается мы не знакомы)")
            elif current["state"] == 2:
                if message.text != current["hash"]:
                    bot.send_sticker(message.chat.id, config["STICKER"]["furious"])
                    bot.send_message(message.chat.id, "Вы не подтвердили свою почту!")
                else:
                    bot.send_sticker(message.chat.id, config["STICKER"]["happy"])
                    bot.send_message(message.chat.id, "Отлично! Все подтвержденно! Используйте /help")
                    server_api.change_state(message.chat.id, 3)
            elif 'найти' in list(map(str.lower, message.text.split())) and current["state"] == 3:
                words = list(map(str.lower, message.text.split()))
                req = " ".join(words[words.index("найти") + 1:])
                bot.send_message(message.chat.id, "Уже ищу :)")
                top10["data"] = filmapi.search_film(req)
                # noinspection PyTypeChecker
                top10["len"] = len(top10["data"])
                markup = types.InlineKeyboardMarkup(row_width=2)
                item1 = types.InlineKeyboardButton("⬅", callback_data='Prev')
                item2 = types.InlineKeyboardButton("➡", callback_data='Next')
                url = server_api.open_full(top10["data"][top10["current"]])
                if url is not None:
                    item3 = types.InlineKeyboardButton("Открыть в браузере", url=url)
                    markup.add(item1, item2, item3)
                else:
                    markup.add(item1, item2)
                bot.send_photo(message.chat.id, photo=top10["data"][top10["current"]]["poster"],
                               caption=f'<b>{top10["data"][top10["current"]]["title"]}</b>\n\n'
                                       f'{top10["data"][top10["current"]]["description"]}\n\n'
                                       f'Rate: {top10["data"][top10["current"]]["vote_average"]}',
                               parse_mode="html", reply_markup=markup)

        else:
            bot.send_sticker(message.chat.id, config["STICKER"]["furious"])
            bot.send_message(message.chat.id, "Вы все еще не зарегестрирвались! /register")
    except TypeError:
        bot.send_sticker(message.chat.id, config["STICKER"]["tired"])
        bot.send_message(message.chat.id, "Извините, бот сейчас устал и не может работать!")


@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    try:
        if call.message:
            markup = types.InlineKeyboardMarkup(row_width=2)
            item1 = types.InlineKeyboardButton("⬅", callback_data='Prev')
            item2 = types.InlineKeyboardButton("➡", callback_data='Next')
            if call.data == 'Prev' and top10["data"] is not None:
                top10["current"] = (top10["current"] - 1) % top10["len"]
                url = server_api.open_full(top10["data"][top10["current"]])
                if url is not None:
                    item3 = types.InlineKeyboardButton("Открыть в браузере", url=url)
                    markup.add(item1, item2, item3)
                else:
                    markup.add(item1, item2)
                bot.send_photo(call.message.chat.id, photo=top10["data"][top10["current"]]["poster"],
                               caption=f'<b>{top10["data"][top10["current"]]["title"]}</b>\n\n'
                                       f'{top10["data"][top10["current"]]["description"]}\n\n'
                                       f'Rate: {top10["data"][top10["current"]]["vote_average"]}',
                               parse_mode="html", reply_markup=markup)
            elif call.data == 'Next' and top10["data"] is not None:
                top10["current"] = (top10["current"] + 1) % top10["len"]
                url = server_api.open_full(top10["data"][top10["current"]])
                if url is not None:
                    item3 = types.InlineKeyboardButton("Открыть в браузере", url=url)
                    markup.add(item1, item2, item3)
                else:
                    markup.add(item1, item2)
                bot.send_photo(call.message.chat.id, photo=top10["data"][top10["current"]]["poster"],
                               caption=f'<b>{top10["data"][top10["current"]]["title"]}</b>\n\n'
                                       f'{top10["data"][top10["current"]]["description"]}\n\n'
                                       f'Rate: {top10["data"][top10["current"]]["vote_average"]}',
                               parse_mode="html", reply_markup=markup)
            elif top10["data"] is None:
                markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
                item1 = types.KeyboardButton("/random")
                item2 = types.KeyboardButton("/top10")
                markup.add(item1, item2)
                bot.send_message(call.message.chat.id, "Похоже я уже забыл, о чем мы говорили. Повторите",
                                 reply_markup=markup)
    except Exception as e:
        print(repr(e))


if __name__ == '__main__':
    while True:
        try:
            filmapi = TMDB(config)
            server_api = RequestServer("http://flask-filmline.herokuapp.com")
            # server_api = RequestServer("http://127.0.0.1:8000")
            bot.polling(none_stop=True)
        except Exception as e:
            bot.stop_bot()
            print("Restarting bot")
        time.sleep(300)
