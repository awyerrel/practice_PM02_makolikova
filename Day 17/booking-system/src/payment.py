def calculate_payment(amount: float, commission: float = 0.1) -> float:
    if amount <= 0:
        return 0.0
    return round(amount + amount * commission, 2)


def refund(amount: float) -> float:
    if amount < 0:
        return 0.0
    return amount