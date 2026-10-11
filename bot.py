import os

import telebot
from dotenv import load_dotenv

from main import run_router

load_dotenv()
BOT_TOKEN = os.environ["BOT_TOKEN"]

bot = telebot.TeleBot(BOT_TOKEN)


@bot.message_handler(commands=['start', 'help'])
def cmd_start(message):
    bot.reply_to(message,
                 'Привет! Я умею: погода в любом городе, калькулятор, заметки и просто поболтать. Пиши словами.')


@bot.message_handler(func=lambda m: True)
def handle_message(message):
    if not message.text:
        bot.reply_to(message, 'Я понимаю только текст')
        return
    try:
        answer = run_router(message.text)
    except Exception as e:
        answer = f'Внутренняя ошибка: {type(e).__name__}: {e}'
    # лимит сообщения Telegram — 4096 символов
    bot.reply_to(message, answer[:4000])


if __name__ == '__main__':
    print('Бот запущен, Ctrl+C — стоп')
    bot.polling(none_stop=True)
