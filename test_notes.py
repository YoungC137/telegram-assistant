import notes
from notes import add_note, read_notes

def test_notes_empty(tmp_path, monkeypatch):
    monkeypatch.setattr(notes, 'NOTES_FILE', tmp_path / 'notes.txt')
    assert read_notes() == []
def test_notes_add(tmp_path, monkeypatch):
    monkeypatch.setattr(notes, 'NOTES_FILE', tmp_path / 'notes.txt')
    add_note('купить хлеб')
    assert read_notes() == ['купить хлеб']