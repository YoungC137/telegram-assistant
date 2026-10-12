from main import _safe_eval,validate_decision
def test_umn():
    assert _safe_eval('2+2*2') == 6
def test_sec():
    assert _safe_eval("__import__('os')") is None
def test_main():
    assert _safe_eval('привет') == None
def test_validate_decision():
    assert isinstance(validate_decision('{"action":"chat","args":{}}'),dict)
def test_validate_decision_no_action():
    assert validate_decision('{"args":{}}') is None
