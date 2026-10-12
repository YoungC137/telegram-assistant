import weather

class FakeResp:
    def raise_for_status(self): pass
    def json(self):
        return {'current': {'temperature_2m': 25.0, 'weather_code': 0}}

def test_weather_mock(monkeypatch):
    monkeypatch.setattr(weather, '_geocode', lambda city: (43.0, 131.0, 'Тестово'))
    monkeypatch.setattr(weather.requests, 'get', lambda *a, **k: FakeResp())
    assert weather.get_weather('Тестово') == (25.0, 0, 'Тестово')