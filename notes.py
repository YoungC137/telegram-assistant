from pathlib import Path

NOTES_FILE = Path(__file__).parent / 'notes.txt'


def add_note(text):
    """Дописывает одну заметку в файл. Одна строка = одна заметка."""
    line = text.strip().replace('\n', ' ')
    if not line:
        return 'Пустая заметка, не сохранил'
    with open(NOTES_FILE, 'a', encoding='utf-8') as f:
        f.write(line + '\n')
    total = len(read_notes())
    return f'Сохранил. Всего заметок: {total}'


def read_notes():
    """Читает все заметки списком строк. Пустой файл — пустой список."""
    if not NOTES_FILE.exists():
        return []
    with open(NOTES_FILE, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip()]
