import sys
from io import BytesIO
import requests
from PIL import Image
from math import radians, sin, cos, acos


# Функция для вычисления расстояния между двумя точками (в километрах)
def calculate_distance(point1, point2):
    """
    Вычисляет расстояние между двумя точками на сфере (в км) по формуле гаверсинусов.
    :param point1: Кортеж (долгота, широта) первой точки.
    :param point2: Кортеж (долгота, широта) второй точки.
    :return: Расстояние в километрах.
    """
    lon1, lat1 = map(radians, point1)
    lon2, lat2 = map(radians, point2)
    distance = acos(sin(lat1) * sin(lat2) + cos(lat1) * cos(lat2) * cos(lon1 - lon2))
    return round(distance * 6371, 2)


# Функция для автоматического позиционирования карты по двум точкам
def auto_position(points):
    """
    Вычисляет центр карты и масштаб (spn) для отображения всех точек.
    :param points: Список кортежей [(долгота, широта), ...].
    :return: Кортеж (центр карты, spn).
    """
    lons, lats = zip(*points)
    min_lon, max_lon = min(lons), max(lons)
    min_lat, max_lat = min(lats), max(lats)
    center_lon = (min_lon + max_lon) / 2
    center_lat = (min_lat + max_lat) / 2
    spn_lon = max_lon - min_lon
    spn_lat = max_lat - min_lat
    return f"{center_lon},{center_lat}", f"{spn_lon},{spn_lat}"


# Параметры командной строки
if len(sys.argv) < 2:
    print("Использование: python find_pharmacy.py 'Москва, ул. Академика Королёва, 12'")
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
    print("Ошибка выполнения запроса:")
    print(response.url)
    sys.exit(1)

json_response = response.json()
toponym = json_response["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"]
address_coords = toponym["Point"]["pos"].split()
address_lon, address_lat = map(float, address_coords)

# ПОИСК АПТЕКИ: Поиск ближайшей аптеки
search_api_server = "https://search-maps.yandex.ru/v1/"
search_params = {
    "apikey": "dda3ddba-c9ea-4ead-9010-f43fbc15c6e3",
    "text": "аптека",
    "lang": "ru_RU",
    "ll": ",".join(address_coords),
    "type": "biz"
}

response = requests.get(search_api_server, params=search_params)
if not response:
    print("Ошибка выполнения запроса:")
    print(response.url)
    sys.exit(1)

json_response = response.json()
pharmacy = json_response["features"][0]
pharmacy_coords = pharmacy["geometry"]["coordinates"]
pharmacy_lon, pharmacy_lat = pharmacy_coords
pharmacy_name = pharmacy["properties"]["CompanyMetaData"]["name"]
pharmacy_address = pharmacy["properties"]["CompanyMetaData"]["address"]
pharmacy_hours = pharmacy["properties"]["CompanyMetaData"].get("Hours", {}).get("text", "Время работы не указано")

# Расчёт расстояния до аптеки
distance = calculate_distance((address_lon, address_lat), (pharmacy_lon, pharmacy_lat))

# Формирование сниппета
snippet = (
    f"Аптека: {pharmacy_name}\n"
    f"Адрес: {pharmacy_address}\n"
    f"Время работы: {pharmacy_hours}\n"     
    f"Расстояние: {distance} км"
)
print(snippet)

# Автоматическое позиционирование карты
points = [(address_lon, address_lat), (pharmacy_lon, pharmacy_lat)]
map_center, map_spn = auto_position(points)

# Собираем параметры для запроса к StaticMapsAPI
map_params = {
    "ll": map_center,
    "spn": map_spn,
    "apikey": "f3a0fe3a-b07e-4840-a1da-06f18b2ddf13",
    "pt": f"{address_lon},{address_lat},pm2rdl~{pharmacy_lon},{pharmacy_lat},pm2bl"
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
