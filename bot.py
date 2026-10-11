import os
import sys

import telebot
from dotenv import load_dotenv

from main import run_router

load_dotenv()
BOT_TOKEN = os.environ["BOT_TOKEN"]

PID_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bot.pid')


def ensure_single_instance():
    """Telegram разрешает только один getUpdates. Не даём подняться второму экземпляру."""
    if os.path.exists(PID_FILE):
        try:
            with open(PID_FILE) as f:
                old_pid = int(f.read().strip())
            os.kill(old_pid, 0)  # проверка живости: SIGNUM 0 ничего не шлёт, но упадёт на мертвом
        except (ValueError, OSError, ProcessLookupError):
            pass  # файл устарел — процесс давно мёртв, перезапишем
        else:
            print(f'Бот уже запущен (PID {old_pid}). Сначала: kill {old_pid}')
            sys.exit(1)
    with open(PID_FILE, 'w') as f:
        f.write(str(os.getpid()))

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
    ensure_single_instance()
    print('Бот запущен, Ctrl+C — стоп')
    try:
        bot.polling(none_stop=True)
    finally:
        # убираем за собой, чтобы следующий старт не считал нас живыми
        try:
            os.remove(PID_FILE)
        except OSError:
            pass
