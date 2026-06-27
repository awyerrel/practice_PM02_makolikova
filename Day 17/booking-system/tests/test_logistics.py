import pytest
from src.logistics import *

def test_distance():
    d = calculate_distance(0, 0, 3, 4)
    assert d == 5.0

def test_distance_invalid_lat():
    assert calculate_distance(200, 0, 0, 0) == -1

def test_time():
    assert estimate_time(120, 60) == 2.0

def test_time_zero():
    assert estimate_time(0, 60) == 0

def test_route_valid():
    points = [{"lat": 10, "lon": 20}]
    assert is_route_valid(points)

def test_route_invalid():
    points = [{"lat": 200, "lon": 20}]
    assert not is_route_valid(points)