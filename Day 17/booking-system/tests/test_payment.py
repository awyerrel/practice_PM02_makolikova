from src.payment import *

def test_payment():
    assert calculate_payment(100) == 110.0

def test_refund():
    assert refund(50) == 50