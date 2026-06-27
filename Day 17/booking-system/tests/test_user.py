from src.user import *

def test_email():
    assert validate_email("test@mail.com")

def test_age():
    assert validate_age(20)