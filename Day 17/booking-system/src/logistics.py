import math

def calculate_distance(lat1, lon1, lat2, lon2):
    if not (-90 <= lat1 <= 90 and -90 <= lat2 <= 90):
        return -1
    if not (-180 <= lon1 <= 180 and -180 <= lon2 <= 180):
        return -1

    return math.sqrt((lat2 - lat1)**2 + (lon2 - lon1)**2)


def estimate_time(distance, speed=60):
    if distance <= 0 or speed <= 0:
        return 0
    return round(distance / speed, 2)


def is_route_valid(points: list):
    if not points:
        return False

    for p in points:
        if "lat" not in p or "lon" not in p:
            return False
        if not (-90 <= p["lat"] <= 90):
            return False
        if not (-180 <= p["lon"] <= 180):
            return False

    return True