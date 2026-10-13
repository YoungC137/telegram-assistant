import ollama

# qwen3:4b-instruct — не-thinking вариант той же модели.
# У qwen3:4b блок рассуждений попадает в content даже при think=False,
# из-за чего json_mode иногда возвращал текст вместо JSON.
MODEL = 'qwen3:4b-instruct'

ROUTER_SYSTEM = (
    'Ты — модуль маршрутизации. '
    'Отвечай СТРОГО одним валидным JSON и больше ничем: '
    'без рассуждений, пояснений и текста до или после объекта.'
)

CHAT_SYSTEM = 'Ты полезный ассистент. Отвечай кратко и по делу.'


# Ollama выгружает модель из видеопамяти через 5 минут простоя (значение по умолчанию).
# Следующий запрос после паузы грузит 2.5 ГБ с диска — это те самые 10-30 секунд
# "иногда тормозит". keep_alive держит модель в памяти между сообщениями.
KEEP_ALIVE = '30m'

# Роутер возвращает короткий JSON, длинный лимит ему не нужен.
# Отдельный бюджет на chat, чтобы болтовня не упиралась в тот же потолок.
ROUTER_TOKENS = 120
CHAT_TOKENS = 250

# ollama.chat() по умолчанию ждёт ответ 15 секунд и бросает ReadTimeout.
# Холодная модель грузится с диска 10-30 секунд — отсюда бралось
# "иногда не работает": первый запрос после простоя гарантированно падал.
# В этом клиенте timeout задаётся на уровне клиента (у ollama.chat()
# такого параметра нет), 120 секунд с запасом покрывают и загрузку,
# и длинную генерацию.
_client = ollama.Client(timeout=120)


def ask_ai(question, json_mode=False, temperature=0):
    """Один запрос к локальной модели.

    json_mode=True — включаем format='json' и системную подсказку,
    чтобы модель не добавляла текст вокруг объекта.
    temperature — 0 для детерминированного роутера; ретраям нужен
    другой температурой, иначе повтор промпта даёт байт в байт тот же ответ.
    """
    response = _client.chat(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": ROUTER_SYSTEM if json_mode else CHAT_SYSTEM
            },
            {
                "role": "user",
                "content": question
            }
        ],
        options={
            "temperature": temperature,
            "num_predict": ROUTER_TOKENS if json_mode else CHAT_TOKENS
        },
        format='json' if json_mode else None,
        keep_alive=KEEP_ALIVE,
    )
    return response['message']['content']


def warm_up():
    """Загружает модель в память заранее, чтобы первый пользователь
    не платил 10-30 секунд за холодный старт. Ошибку не поднимаем:
    Ollama может быть ещё не готова — бот всё равно должен подниматься."""
    try:
        _client.chat(
            model=MODEL,
            messages=[{'role': 'user', 'content': 'ok'}],
            options={'num_predict': 1},
            keep_alive=KEEP_ALIVE,
        )
        print('Модель прогрета и в памяти.')
    except Exception as e:
        print(f'Прогрев не удался: {type(e).__name__}: {e}. '
              'Первый запрос может быть долгим или Ollama не запущена.')