import telebot
import configparser

config = configparser.ConfigParser()
config.read("settings.ini")

bot = telebot.TeleBot(config["BOT"]["token"])


@bot.message_handler(commands=["start"])
def repeat_all_messages(message):
    bot.send_sticker(message.chat_id, file_id=config["STICKER"]["hello"])
    bot.send_message(message.chat.id, "Привет, тебе нужно зарегестрироваться прежде, чем начать!\nДля регистрации "
                                      "/register")


if __name__ == '__main__':
    bot.polling(none_stop=True)