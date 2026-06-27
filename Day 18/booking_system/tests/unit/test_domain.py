"""
Unit-тесты для доменных моделей
"""
import pytest
from datetime import datetime, timedelta
from src.core.domain import (
    Coordinates, Location, RouteSegment, Route,
    TransportType, Hotel
)
from src.core.exceptions import ValidationError


class TestCoordinates:
    """Тесты для Value Object Coordinates"""
    
    def test_coordinates_creation_valid(self):
        """Создание координат с валидными значениями"""
        coords = Coordinates(55.7558, 37.6173)
        assert coords.lat == 55.7558
        assert coords.lon == 37.6173
    
    def test_coordinates_creation_invalid_lat(self):
        """Создание координат с невалидной широтой"""
        with pytest.raises(ValidationError):
            Coordinates(100, 37.6173)
        
        with pytest.raises(ValidationError):
            Coordinates(-100, 37.6173)
    
    def test_coordinates_creation_invalid_lon(self):
        """Создание координат с невалидной долготой"""
        with pytest.raises(ValidationError):
            Coordinates(55.7558, 200)
        
        with pytest.raises(ValidationError):
            Coordinates(55.7558, -200)
    
    def test_distance_to_zero(self):
        """Расстояние до самой себя"""
        coords = Coordinates(55.7558, 37.6173)
        assert coords.distance_to(coords) == 0.0
    
    def test_distance_to_moscow_spb(self):
        """Расстояние Москва-СПб"""
        moscow = Coordinates(55.7558, 37.6173)
        spb = Coordinates(59.9343, 30.3351)
        distance = moscow.distance_to(spb)
        # Ожидаемое расстояние ~634 км
        assert 630 < distance < 640
    
    def test_distance_to_with_negative_coords(self):
        """Расстояние с отрицательными координатами"""
        sydney = Coordinates(-33.8688, 151.2093)
        melbourne = Coordinates(-37.8136, 144.9631)
        distance = sydney.distance_to(melbourne)
        # Ожидаемое расстояние ~713 км
        assert 700 < distance < 720


class TestRouteSegment:
    """Тесты для сегмента маршрута"""
    
    def test_route_segment_creation(self):
        """Создание сегмента маршрута"""
        start = Location(id=1, name="Start", coordinates=Coordinates(55.7558, 37.6173))
        end = Location(id=2, name="End", coordinates=Coordinates(59.9343, 30.3351))
        
        segment = RouteSegment(start, end, TransportType.CAR)
        
        assert segment.start == start
        assert segment.end == end
        assert segment.transport_type == TransportType.CAR
        assert segment.distance_km > 0
        assert segment.duration_min > 0
    
    def test_route_segment_with_specific_distance(self):
        """Создание сегмента с заданным расстоянием"""
        start = Location(id=1, name="Start")
        end = Location(id=2, name="End")
        
        segment = RouteSegment(start, end, TransportType.WALK, distance_km=10)
        
        assert segment.distance_km == 10
        # Длительность должна быть рассчитана автоматически
        assert segment.duration_min > 0
    
    def test_route_segment_with_zero_speed(self):
        """Тест с нулевой скоростью - должен быть дефект"""
        start = Location(id=1, name="Start", coordinates=Coordinates(55.7558, 37.6173))
        end = Location(id=2, name="End", coordinates=Coordinates(55.7598, 37.6203))
        
        # ОШИБКА 2: будет деление на ноль при расчете времени
        # Этот тест должен упасть
        segment = RouteSegment(start, end, TransportType.CAR)
        assert segment.duration_min > 0


class TestRoute:
    """Тесты для агрегата Route"""
    
    def test_route_creation(self):
        """Создание маршрута"""
        route = Route()
        assert route.segments == []
        assert route.total_distance == 0
        assert route.total_duration == 0
    
    def test_route_add_segment(self):
        """Добавление сегмента в маршрут"""
        start = Location(id=1, name="Start", coordinates=Coordinates(55.7558, 37.6173))
        end = Location(id=2, name="End", coordinates=Coordinates(59.9343, 30.3351))
        
        segment = RouteSegment(start, end, TransportType.CAR)
        route = Route()
        route.add_segment(segment)
        
        assert len(route.segments) == 1
        assert route.total_distance == segment.distance_km
        # ОШИБКА 3: total_duration умножается на 2
        assert route.total_duration == segment.duration_min * 2
    
    def test_route_calculate_totals(self):
        """Пересчет общих показателей"""
        start1 = Location(id=1, name="Start", coordinates=Coordinates(55.7558, 37.6173))
        mid = Location(id=2, name="Mid", coordinates=Coordinates(56.8389, 60.6057))
        end = Location(id=3, name="End", coordinates=Coordinates(59.9343, 30.3351))
        
        seg1 = RouteSegment(start1, mid, TransportType.CAR)
        seg2 = RouteSegment(mid, end, TransportType.CAR)
        
        route = Route(segments=[seg1, seg2])
        route.calculate_totals()
        
        expected_distance = seg1.distance_km + seg2.distance_km
        assert route.total_distance == expected_distance
        # ОШИБКА 3: total_duration умножается на 2
        expected_duration = (seg1.duration_min + seg2.duration_min) * 2
        assert route.total_duration == expected_duration
    
    def test_route_get_estimated_arrival(self):
        """Расчет времени прибытия"""
        route = Route()
        route.total_duration = 120  # 2 часа
        departure = datetime(2026, 6, 27, 10, 0)
        arrival = route.get_estimated_arrival(departure)
        
        expected = departure + timedelta(minutes=120)
        assert arrival == expected


class TestHotel:
    """Тесты для сущности Hotel"""
    
    def test_hotel_creation(self):
        """Создание отеля"""
        location = Location(id=1, name="Test Location")
        hotel = Hotel(
            id=1,
            name="Test Hotel",
            location=location,
            rating=4.5,
            price_per_night=150.0,
            available_rooms=10,
            amenities=["WiFi", "Pool", "Restaurant"]
        )
        
        assert hotel.id == 1
        assert hotel.name == "Test Hotel"
        assert hotel.location == location
        assert hotel.rating == 4.5
        assert hotel.price_per_night == 150.0
        assert hotel.available_rooms == 10
        assert len(hotel.amenities) == 3
    
    def test_hotel_with_defaults(self):
        """Создание отеля со значениями по умолчанию"""
        hotel = Hotel(name="Test Hotel")
        assert hotel.id is None
        assert hotel.location is None
        assert hotel.rating == 0.0
        assert hotel.price_per_night == 0.0
        assert hotel.available_rooms == 0
        assert hotel.amenities == []