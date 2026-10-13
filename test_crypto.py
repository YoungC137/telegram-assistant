import crypto
class FakeResp:
    def json(self):
        return {'bitcoin':{'rub':7000000}}
def test_crypto_mock(monkeypatch):
    monkeypatch.setattr(crypto.requests,'get',lambda *a,**k:FakeResp())
    crypto._cache.clear()
    price = crypto.get_price('bitcoin')
    assert price == 7000000
    assert 'bitcoin' in crypto._cache
    assert crypto._cache['bitcoin'][1] == 7000000