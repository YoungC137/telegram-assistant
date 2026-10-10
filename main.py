import json
from ai_2 import ask_ai
from weather import get_weather
from notes import add_note, read_notes
import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.environ["BOT_TOKEN"]

def build_router_prompt(text):
    """Собирает промпт для роутера из реестров tools и tool_args."""
    names = ', '.join(tools)
    desc = '\n'.join(
        f"- {name}: аргументы " + (
            ', '.join(f'{k} ({hint})' for k, hint in args.items()) or 'не нужны'
        )
        for name, args in tool_args.items()
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
    except (json.JSONDecodeError,TypeError):
        return None
    if not isinstance(decision, dict) or (not 'action' in decision ) or (not 'args' in decision):
        return None
    if decision['action'] not in tools:
        return None
    if not isinstance(decision['args'], dict):
        return None
    required = tool_args[decision['action']]
    if decision['action'] != 'chat':
        missing = [k for k in required if k not in decision['args']]
        if missing:
            return None
    return decision
def run_weather(city):
    try:
        temp, code, name = get_weather(city)
        print(f'Погода в {name}: {temp}°C, код погоды {code}')
    except Exception as e:
        print(f'Ошибка получения погоды: {e}')

def run_chat(text):
    answer = ask_ai(f"Ответь на вопрос пользователя: {text}")
    print(answer)

def run_calc(expression):
    result = _safe_eval(expression)
    if result is not None:
        print(f"= {result}")
    else:
        print("Не удалось посчитать локально, спросил у AI:")
        answer = ask_ai(f"Посчитай аккуратно: {expression}")
        print(answer)

def run_notes_add(text):
    print(add_note(str(text)))

def run_notes_show():
    notes = read_notes()
    if not notes:
        print('Заметок пока нет')
        return
    for i, note in enumerate(notes, 1):
        print(f'{i}. {note}')

tools = {
    'weather': run_weather,
    'calc': run_calc,
    'notes_add': run_notes_add,
    'notes_show': run_notes_show,
    'chat': run_chat
}

# какие аргументы ждёт каждое действие: используется в промпте и в normalize_args
tool_args = {
    'weather': {'city': 'город, например Владивосток'},
    'calc': {'expression': 'математическое выражение, например 2+2*2'},
    'notes_add': {'text': 'текст заметки одним предложением'},
    'notes_show': {},
    'chat': {'text': 'исходный запрос пользователя дословно'},
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
    """Спрашивает AI, пока ответ не пройдёт validator. Возвращает сырую строку или None."""
    for attempt in range(max_attempts):
        raw = ask_ai(prompt, json_mode=True)
        if validator(raw):
            return raw
        print(f'Попытка {attempt + 1} провалилась')
    print('Попытки закончились, возвращаю None')
    return None

def normalize_args(action, args, user_text):
    """Оставляет только известные поля. Для chat текст по умолчанию — исходный запрос."""
    if action == 'chat':
        return {'text': args.get('text') or user_text}
    return {k: v for k, v in args.items() if k in tool_args[action]}

def run_router(text):
    raw = ask_with_retry(build_router_prompt(text), validate_decision)
    decision = validate_decision(raw)
    if decision is None:
        print('AI трижды вернула невалидное решение, fallback в chat')
        return run_chat(text)
    action = decision['action']
    args = normalize_args(action, decision['args'], text)
    print(f'Действие: {action}, args: {args}')
    try:
        tools[action](**args)
    except Exception as e:
        print(f'Ошибка выполнения действия: {type(e).__name__}: {e}')


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
        run_router(text)


if __name__ == '__main__':
    main()