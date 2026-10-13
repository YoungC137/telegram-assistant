import json
import os
from ai_2 import ask_ai
from weather import get_weather
from notes import add_note, read_notes
from dotenv import load_dotenv

# .env рядом со скриптом, а не в текущей папке: файл должен находиться,
# откуда бы его ни запустили (python3 main.py, python3 bot.py, cron).
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env'))

# BOT_TOKEN отсюда убран: в main.py он не используется, а строка
# os.environ["BOT_TOKEN"] падала с KeyError при импорте файла без .env —
# это роняло и bot.py, который импортирует main.

def build_router_prompt(text):
    names = ', '.join(tools)
    desc = '\n'.join(
        f"- {name}: аргументы " + (
            ', '.join(f'{k} ({hint})' for k, hint in t['args'].items()) or 'не нужны'
        )
        for name, t in tools.items()
    )
    return f'''
Выбери действие для запроса: {text}

Возможные действия (в поле action пиши название точь-в-точь из списка, своими словами нельзя):
{names}

Аргументы каждого действия (в поле args используй ТОЛЬКО эти имена полей):
{desc}

Если у действия нет аргументов, верни пустой объект: "args": {{}}

Верни строго JSON с двойными кавычками:
{{
   "action": "название действия из списка",
   "args": {{"имя_аргумента": "значение"}}
}}
'''

def validate_decision(raw):
    if raw is None:
        return None
    try:
        decision = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return None
    if not isinstance(decision, dict) or 'action' not in decision or 'args' not in decision:
        return None
    if decision['action'] not in tools:
        return None
    if not isinstance(decision['args'], dict):
        return None
    required = tools[decision['action']]['args']
    missing = [k for k in required if k not in decision['args']]
    if missing:
        return None
    return decision

def run_weather(city):
    try:
        temp, code, name = get_weather(city)
        return f'Погода в {name}: {temp}°C, код погоды {code}'
    except Exception as e:
        return f'Ошибка получения погоды: {e}'

def run_chat(text):
    prompt = f"Ответь коротко, 1-2 предложения, без рассуждений. Вопрос: {text}"
    try:
        answer = ask_ai(prompt)
    except Exception as e:
        # Без этого исключение уходит в bot.py и пользователь видит
        # 'Внутренняя ошибка: ConnectionError' вместо внятной подсказки.
        return f'Локальная модель недоступна ({type(e).__name__}). Проверь, что Ollama запущена.'
    return answer or 'Модель вернула пустой ответ. Проверь, что модель на месте: ollama list'

def run_calc(expression):
    result = _safe_eval(expression)
    if result is not None:
        return f"= {result}"
    return "Не удалось посчитать это выражение локально"

def run_notes_add(text):
    return add_note(str(text))

def run_notes_show():
    notes = read_notes()
    if not notes:
        return 'Заметок пока нет'
    return '\n'.join(f'{i}. {note}' for i, note in enumerate(notes, 1))


tools = {
    'weather':  {'func': run_weather, 'args': {'city': 'город, например Владивосток'}},
    'calc':     {'func': run_calc,    'args': {'expression': 'математическое выражение, например 2+2*2'}},
    'notes_add':{'func': run_notes_add, 'args': {'text': 'текст заметки одним предложением'}},
    'notes_show':{'func': run_notes_show, 'args': {}},
    'chat':     {'func': run_chat,    'args': {'text': 'исходный запрос пользователя дословно'}},
}


def _safe_eval(expr):
    """Безопасно считает выражение. Возвращает число или None."""
    import ast, operator
    _OPS = {ast.Add: operator.add, ast.Sub: operator.sub, 
            ast.Mult: operator.mul, ast.Div: operator.truediv,
            ast.FloorDiv: operator.floordiv, ast.Mod: operator.mod,
            ast.Pow: operator.pow, ast.USub: operator.neg}
    _SAFE_NODES = set(_OPS.keys()) | {ast.Constant, ast.BinOp, ast.UnaryOp}
    def _eval_node(node):
        if type(node) not in _SAFE_NODES:
            raise ValueError("Небезопасная операция")
        if isinstance(node, ast.Constant):
            if not isinstance(node.value, (int, float)):
                raise ValueError("Только числа")
            return node.value
        if isinstance(node, ast.BinOp):
            op = _OPS.get(type(node.op))
            if op is None:
                raise ValueError(f"Оператор {type(node.op).__name__} запрещён")
            return op(_eval_node(node.left), _eval_node(node.right))
        if isinstance(node, ast.UnaryOp):
            op = _OPS.get(type(node.op))
            if op is None:
                raise ValueError(f"Унарный оператор {type(node.op).__name__} запрещён")
            return op(_eval_node(node.operand))
    try:
        tree = ast.parse(expr.strip(), mode='eval')
        return _eval_node(tree.body)
    except Exception:
        return None

  
def ask_with_retry(prompt, validator, max_attempts=3):
    last_raw = None
    for attempt in range(max_attempts):
        if attempt == 0:
            current, temp = prompt, 0
        else:
            # При temperature=0 повтор того же промпта возвращает байт в байт
            # тот же ответ: три попытки превращались в тройную задержку без
            # шанса на другой результат. На повторе меняем и подсказку, и температуру.
            current = prompt + (
                '\n\nПрошлый ответ не прошёл проверку. Верни ТОЛЬКО объект вида '
                '{"action": "...", "args": {...}} без текста до и после него.'
            )
            temp = 0.7
        last_raw = ask_ai(current, json_mode=True, temperature=temp)
        if validator(last_raw):
            return last_raw
        print(f'Попытка {attempt + 1} провалилась')
    # Валидный ответ так и не получили. Логируем, что именно вернула модель,
    # иначе фолбэк в chat выглядит как тихая потеря намерения пользователя.
    print(f'РОУТЕР ИСЧЕРПАЛ ПОПЫТКИ. Последний ответ модели: {str(last_raw)[:300]!r}')
    return None

def normalize_args(action, args, user_text):
    """Оставляет только известные поля."""
    return {k: v for k, v in args.items() if k in tools[action]['args']}

def run_router(text):
    try:
        raw = ask_with_retry(build_router_prompt(text), validate_decision)
    except Exception as e:
        return f'Локальная модель недоступна ({type(e).__name__}). Проверь, что Ollama запущена.'
    decision = validate_decision(raw)
    if decision is None:
        return 'AI трижды вернула невалидное решение. ' + run_chat(text)
    action = decision['action']
    args = normalize_args(action, decision['args'], text)
    print(f'Действие: {action}, args: {args}')
    try:
        return tools[action]['func'](**args)
    except Exception as e:
        return f'Ошибка выполнения действия: {type(e).__name__}: {e}'


def main():
    print('Ассистент запущен. Для выхода — exit')
    while True:
        try:
            text = input("Введите запрос: ")
            if not text:continue
            if text == 'quit' or text == 'exit':
                break
        except KeyboardInterrupt:
            break
        print(run_router(text))


if __name__ == '__main__':
    main()