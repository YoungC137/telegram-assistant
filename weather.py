import requests
url = "https://api.open-meteo.com/v1/forecast"

DEFAULT_LAT = 43.12
DEFAULT_LON = 131.89

def _geocode(city):
    resp = requests.get(
        "https://geocoding-api.open-meteo.com/v1/search",
        params={'name': city, 'count': 1, 'language': 'ru'},
        timeout=10
    )
    if resp.status_code != 200:
        return None
    data = resp.json()
    results = data.get('results', [])
    if not results:
        return None
    r = results[0]
    return r['latitude'], r['longitude'], r.get('name', city)

def get_weather(city=None):
    if city:
        found = _geocode(city)
        if found is None:
            # Молча подменить город дефолтным — это неправдивый ответ:
            # пользователь просил Пекин, а получил погоду во Владивостоке.
            raise ValueError(f'Город {city!r} не найден')
        lat, lon, name = found
    else:
        lat, lon, name = DEFAULT_LAT, DEFAULT_LON, 'Владивосток'
    resp = requests.get(url, params={
        'latitude': lat,
        'longitude': lon,
        'current': 'temperature_2m,weather_code'
    }, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    return data['current']['temperature_2m'], data['current']['weather_code'], name