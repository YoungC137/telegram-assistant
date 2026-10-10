import requests
url = "https://api.open-meteo.com/v1/forecast"

DEFAULT_LAT = 43.12
DEFAULT_LON = 131.89

def _geocode(city):
    resp = requests.get(
        "https://geocoding-api.open-meteo.com/v1/search",
        params={'name': city, 'count': 1},
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
        lat, lon, name = _geocode(city) or (DEFAULT_LAT, DEFAULT_LON, city)
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