# map_utils.py

def calculate_spn(toponym):
    """
    Вычисляет параметр spn (размер области карты) на основе данных о границах объекта.
    :param toponym: JSON-объект, представляющий топоним из ответа геокодера.
    :return: Кортеж (широта, долгота) для параметра spn.
    """
    # Получаем координаты углов описывающего прямоугольника
    envelope = toponym["boundedBy"]["Envelope"]
    lower_corner = envelope["lowerCorner"].split()
    upper_corner = envelope["upperCorner"].split()

    # Вычисляем разницу между углами
    longitude_diff = abs(float(upper_corner[0]) - float(lower_corner[0]))
    latitude_diff = abs(float(upper_corner[1]) - float(lower_corner[1]))

    return longitude_diff, latitude_diff