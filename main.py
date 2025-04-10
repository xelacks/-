import sys
from io import BytesIO
import requests
from PIL import Image
from map_utils import calculate_spn  # Импортируем функцию из отдельного файла

# Пусть наше приложение предполагает запуск:
# python search.py Москва, ул. Ак. Королева, 12
toponym_to_find = " ".join(sys.argv[1:])

geocoder_api_server = "http://geocode-maps.yandex.ru/1.x/"
geocoder_params = {
    "apikey": "8013b162-6b42-4997-9691-77b7074026e0",
    "geocode": toponym_to_find,
    "format": "json"
}

response = requests.get(geocoder_api_server, params=geocoder_params)

if not response:
    print("Ошибка выполнения запроса:")
    print(response.url)
    sys.exit(1)

# Преобразуем ответ в json-объект
json_response = response.json()
toponym = json_response["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"]

# Координаты центра топонима
toponym_coordinates = toponym["Point"]["pos"]
toponym_longitude, toponym_latitude = toponym_coordinates.split()

# Вычисляем параметр spn
longitude_diff, latitude_diff = calculate_spn(toponym)
spn = f"{longitude_diff},{latitude_diff}"

# Собираем параметры для запроса к StaticMapsAPI
map_params = {
    "ll": ",".join([toponym_longitude, toponym_latitude]),
    "spn": spn,
    "apikey": "f3a0fe3a-b07e-4840-a1da-06f18b2ddf13",
    "pt": f"{toponym_longitude},{toponym_latitude},pm2rdl"  # Добавляем точку на карту
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