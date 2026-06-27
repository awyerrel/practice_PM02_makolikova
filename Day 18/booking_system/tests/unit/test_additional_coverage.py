import pytest
from src.core.domain import Coordinates, Location


class TestAdditionalCoverage:
    
    def test_coordinates_equal(self):
        c1 = Coordinates(55.7558, 37.6173)
        c2 = Coordinates(55.7558, 37.6173)
        c3 = Coordinates(59.9343, 30.3351)
        assert c1 == c2
        assert c1 != c3
    
    def test_coordinates_hash(self):
        c1 = Coordinates(55.7558, 37.6173)
        c2 = Coordinates(55.7558, 37.6173)
        assert hash(c1) == hash(c2)
    
    def test_coordinates_repr(self):
        c = Coordinates(55.7558, 37.6173)
        assert repr(c) == "Coordinates(lat=55.7558, lon=37.6173)"
    
    def test_location_get_distance_to(self):
        loc1 = Location(name="Moscow", coordinates=Coordinates(55.7558, 37.6173))
        loc2 = Location(name="SPb", coordinates=Coordinates(59.9343, 30.3351))
        distance = loc1.get_distance_to(loc2)
        assert 630 < distance < 640
    
    def test_location_get_distance_to_no_coords(self):
        loc1 = Location(name="Moscow")
        loc2 = Location(name="SPb")
        distance = loc1.get_distance_to(loc2)
        assert distance == 0.0