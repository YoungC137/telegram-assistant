import os
import subprocess
import sys
import threading
import time

import telebot
from dotenv import load_dotenv

from ai_2 import ask_ai  # noqa: F401  # импорт заодно грузит .env с AI_API_KEY
from main import run_router

# .env ищем рядом со скриптом, а не в текущей папке: load_dotenv() без пути
# берёт её откуда запущен процесс. python3 bot.py из домашней папки — файл
# не найден, BOT_TOKEN падает с KeyError, бот мёртв на старте без внятной причины.
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env'))
BOT_TOKEN = os.environ["BOT_TOKEN"]

PID_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bot.pid')


def _pid_is_our_bot(pid):
    """Жив ли под этим PID именно наш bot.py.

    Одной проверки os.kill(pid, 0) мало: macOS переиспользует номера PID.
    В устаревшем bot.pid может лежать номер, который уже отдали другой
    программе — бот решит, что он запущен, и откажется стартовать навсегда.
    """
    try:
        out = subprocess.run(
            ['ps', '-p', str(pid), '-o', 'command='],
            capture_output=True, text=True, timeout=5
        ).stdout
    except Exception:
        return False
    return 'bot.py' in out


def ensure_single_instance():
    """Telegram разрешает только один getUpdates. Не даём подняться второму экземпляру."""
    if os.path.exists(PID_FILE):
        try:
            with open(PID_FILE) as f:
                old_pid = int(f.read().strip())
        except ValueError:
            old_pid = None  # в файле мусор — перезапишем
        if old_pid and _pid_is_our_bot(old_pid):
            print(f'Бот уже запущен (PID {old_pid}). Сначала: kill {old_pid}')
            sys.exit(1)
        # файл устарел: процесс мёртв или PID достался другой программе
    with open(PID_FILE, 'w') as f:
        f.write(str(os.getpid()))

class BotErrorHandler(telebot.ExceptionHandler):
    """Последняя линия обороны polling.

    Без неё любое непойманное исключение из обработчика пробивает
    bot.polling() насквозь (внутри telebot это except Exception -> raise),
    процесс умирает молча, а сообщение уже съедено с offset — потеряно.
    Возврат True говорит telebot: ошибку обработали, крути polling дальше.
    """

    def handle(self, exception):
        print(f'Необработанная ошибка обработчика: {type(exception).__name__}: {exception}')
        return True


bot = telebot.TeleBot(BOT_TOKEN, exception_handler=BotErrorHandler())


@bot.message_handler(commands=['start', 'help'])
def cmd_start(message):
    bot.reply_to(message,
                 'Привет! Я умею: погода в любом городе, калькулятор, заметки и просто поболтать. Пиши словами.')


def _keep_typing(chat_id, stop_event):
    """Держит индикатор «печатает…» всё время, пока считается ответ.

    Telegram гасит статус через ~5 секунд после одного send_chat_action,
    а модель на 4B может думать и дольше — без повтора бот выглядит
    зависшим, хотя честно считает. Поток шлёт статус каждые 4 секунды,
    пока основной поток не попросит остановиться.
    """
    while not stop_event.is_set():
        try:
            bot.send_chat_action(chat_id, 'typing')
        except Exception:
            return  # статус — косметика, ронять из-за неё обработку не стоит
        stop_event.wait(4)


@bot.message_handler(func=lambda m: True)
def handle_message(message):
    if not message.text:
        bot.reply_to(message, 'Я понимаю только текст')
        return
    stop_typing = threading.Event()
    threading.Thread(target=_keep_typing, args=(message.chat.id, stop_typing), daemon=True).start()
    start = time.time()
    try:
        answer = run_router(message.text)
    except Exception as e:
        answer = f'Внутренняя ошибка: {type(e).__name__}: {e}'
    finally:
        stop_typing.set()
    # Замер держим в логе: без него "тормозит" остаётся ощущением,
    # а с числами видно, просела модель, поиск города или сеть.
    print(f'[{time.time() - start:.1f}с] {message.text[:40]!r} -> {answer[:60]!r}')
    # лимит сообщения Telegram — 4096 символов
    bot.reply_to(message, answer[:4000])


if __name__ == '__main__':
    ensure_single_instance()
    # Прогрев не нужен: модель крутится на сервере Groq, а не в нашей памяти.
    print('Бот запущен, Ctrl+C — стоп')
    try:
        bot.polling(none_stop=True)
    finally:
        # убираем за собой, чтобы следующий старт не считал нас живыми
        try:
            os.remove(PID_FILE)
        except OSError:
            pass
