# Telegram-ассистент

Бот в Telegram на локальной нейросети: понимает запросы обычным текстом и сам выбирает, какой инструмент применить.

## Что умеет

- Погода в любом городе
- Курс криптовалют (биткоин, эфириум и другие) в рублях
- Калькулятор математических выражений
- Заметки: добавить, посмотреть список
- Свободная беседа

## Стек

Python 3 · Ollama (qwen3:4b) · pyTelegramBotAPI · requests · pytest

## Установка и запуск

1. Клонировать и установить зависимости:

```bash
git clone https://github.com/YoungC137/telegram-assistant.git
cd telegram-assistant
pip install -r requirements.txt
```

2. Создать `.env` по образцу и вписать токен от @BotFather:

```bash
cp .env.example .env
```

3. Запустить Ollama с моделью:

```bash
ollama pull qwen3:4b-instruct
ollama serve
```

4. Запустить бота:

```bash
python3 bot.py
```

## Тесты

```bash
python3 -m pytest -v
```

Тесты не требуют ни Ollama, ни Telegram — внешние вызовы закрыты моками, поэтому прогоняются где угодно, включая GitHub Actions.
