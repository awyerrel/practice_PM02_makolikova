def calculate_discount(price: float, nights: int, is_vip: bool = False) -> float:
    if price <= 0 or nights <= 0:
        return 0.0

    base_discount = (nights // 3) * 10
    vip_bonus = 5 if is_vip else 0
    total_discount = min(base_discount + vip_bonus, 50)

    return price * (total_discount / 100)


def calculate_total_with_tax(price: float, tax_rate: float = 0.18) -> float:
    if price < 0:
        return 0.0
    return round(price * (1 + tax_rate), 2)


def calculate_average_rating(ratings: list) -> float:
    if not ratings:
        return 0.0
    return sum(ratings) / len(ratings)


def is_room_available(bookings: list, check_in, check_out, room_id: int) -> bool:
    for b in bookings:
        if b["room_id"] != room_id:
            continue

        if b["check_in"] < check_out and b["check_out"] > check_in:
            return False

    return True