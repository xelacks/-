import sys
from io import BytesIO
import requests
from PIL import Image


# Функция для форматирования цвета метки в зависимости от времени работы
def get_marker_color(hours):
    if not hours:
        return "gr"  # Серый цвет (если данных о времени работы нет)
    text = hours.get("text", "").lower()
    if "круглосуточно" in text or "24 часа" in text:
        return "gn"  # Зелёный цвет (круглосуточные аптеки)
    return "bl"  # Синий цвет (некруглосуточные аптеки)


# Параметры командной строки
if len(sys.argv) < 2:
    print("Использование: python find_pharmacies.py 'адрес'")
    sys.exit(1)

address = " ".join(sys.argv[1:])

# ГЕОКОДЕР: Поиск координат исходного адреса
geocoder_api_server = "http://geocode-maps.yandex.ru/1.x/"
geocoder_params = {
    "apikey": "8013b162-6b42-4997-9691-77b7074026e0",
    "geocode": address,
    "format": "json"
}

response = requests.get(geocoder_api_server, params=geocoder_params)
if not response:
    print("Ошибка выполнения запроса к геокодеру:")
    print(response.url)
    sys.exit(1)

json_response = response.json()
toponym = json_response["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"]
address_coords = toponym["Point"]["pos"].split()
address_lon, address_lat = map(float, address_coords)

# ПОИСК АПТЕК: Поиск 10 ближайших аптек
search_api_server = "https://search-maps.yandex.ru/v1/"
search_params = {
    "apikey": "dda3ddba-c9ea-4ead-9010-f43fbc15c6e3",
    "text": "аптека",
    "lang": "ru_RU",
    "ll": ",".join(map(str, address_coords)),
    "type": "biz",
    "results": 10  # Ищем 10 аптек
}

response = requests.get(search_api_server, params=search_params)
if not response:
    print("Ошибка выполнения запроса к API поиска:")
    print(response.url)
    sys.exit(1)

json_response = response.json()
pharmacies = json_response["features"]

# Формируем параметры для карты
map_points = []
for pharmacy in pharmacies:
    coords = pharmacy["geometry"]["coordinates"]
    lon, lat = coords
    hours = pharmacy["properties"]["CompanyMetaData"].get("Hours", {})
    color = get_marker_color(hours)
    map_points.append(f"{lon},{lat},pm2{color}l")  # Корректный формат метки

# Добавляем исходный адрес (красная метка)
map_points.append(f"{address_lon},{address_lat},pm2rdl")

# Автоматическое позиционирование карты
lons, lats = zip(*[list(map(float, point.split(",")[:2])) for point in map_points])
min_lon, max_lon = min(lons), max(lons)
min_lat, max_lat = min(lats), max(lats)
center_lon = (min_lon + max_lon) / 2
center_lat = (min_lat + max_lat) / 2
spn_lon = max_lon - min_lon
spn_lat = max_lat - min_lat

# Собираем параметры для запроса к StaticMapsAPI
map_params = {
    "ll": f"{center_lon},{center_lat}",
    "spn": f"{spn_lon},{spn_lat}",
    "apikey": "f3a0fe3a-b07e-4840-a1da-06f18b2ddf13",
    "pt": "~".join(map_points)  # Все точки через тильду
}

map_api_server = "https://static-maps.yandex.ru/v1"
response = requests.get(map_api_server, params=map_params)

if not response:
    print("Ошибка выполнения запроса к StaticAPI:")
    print(response.url)
    sys.exit(1)

# Отображаем карту
im = BytesIO(response.content)
opened_image = Image.open(im)
opened_image.show()
