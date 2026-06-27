import re

def validate_email(email: str) -> bool:
    return bool(re.match(r"[^@]+@[^@]+\.[^@]+", email))


def validate_age(age: int) -> bool:
    return 18 <= age <= 120