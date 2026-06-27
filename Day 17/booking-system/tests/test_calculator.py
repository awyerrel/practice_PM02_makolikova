import pytest
from src.calculator import *

def test_discount():
    assert calculate_discount(1000, 3) == 100

def test_tax():
    assert calculate_total_with_tax(1000) == 1180.0

def test_rating():
    assert calculate_average_rating([4,5]) == 4.5

def test_room():
    bookings = [{"room_id":1,"check_in":"1","check_out":"3"}]
    assert is_room_available(bookings,"3","4",1)