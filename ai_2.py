import os

from dotenv import load_dotenv
from openai import OpenAI

# .env ищем рядом с этим файлом: импорт из другой папки (тесты, CI)
# не должен падать с KeyError — тут мы потеряли полдня ещё на weather.
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env'))

# HuggingFace Inference (бесплатный токен, работает без VPN).
# Groq и OpenRouter отсюда блокируются провайдером (403), проверено живьём.
# Токен: huggingface.co -> Settings -> Access Tokens -> Create new token
BASE_URL = "https://router.huggingface.co/v1"
MODEL = "Qwen/Qwen2.5-7B-Instruct"

SYSTEM = "Ты — модуль маршрутизации. Отвечай СТРОГО одним валидным JSON и больше ничем."
CHAT_SYSTEM = "Ты полезный ассистент. Отвечай кратко и по делу."


def _client():
    # Ключ читаем при первом запросе, а не при импорте модуля:
    # в CI (GitHub Actions) нет .env, и импорт main.py в тестах
    # падал бы с KeyError ещё до первого теста.
    api_key = os.environ.get("AI_API_KEY")
    if not api_key:
        raise RuntimeError(
            'В .env нет AI_API_KEY. Получи бесплатный ключ на '
            'https://console.groq.com/keys и добавь строку AI_API_KEY=...'
        )
    return OpenAI(api_key=api_key, base_url=BASE_URL)


def ask_ai(text, json_mode=False, temperature=None):
    # temperature=None — исторический параметр из main.ask_with_retry:
    # первая попытка детерминированная, ретраи с температурой.
    if temperature is None:
        temperature = 0 if json_mode else 0.7
    resp = _client().chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM if json_mode else CHAT_SYSTEM},
            {"role": "user", "content": text},
        ],
        temperature=temperature,
        max_tokens=120 if json_mode else 250,
        response_format={"type": "json_object"} if json_mode else None,
    )
    return resp.choices[0].message.content