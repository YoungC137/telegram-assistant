import time
import requests

CACHE_TTL = 60
_cache = {}
URL = 'https://api.coingecko.com/api/v3/simple/price'
def get_price(coin):
    now = time.time()
    if coin in _cache and now - _cache[coin][0]<CACHE_TTL:
            return _cache[coin][1]
    last_error = None
    for attempt in range(3):
          try:
            response = requests.get(URL, params={'ids': coin, 'vs_currencies': 'rub'}, timeout=10)
            data = response.json()
            price = data[coin]['rub']
            _cache[coin] = (now, price)
            return price
          except Exception as e:
              last_error = e
              time.sleep(2 ** attempt)
    raise ValueError(f'Не удалось получить цену:{coin} после 3 попыток')from last_error
