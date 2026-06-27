import pytest
from src.core.domain import (
    Coordinates, Location, RouteSegment, Route, TransportType
)
from src.application.services import RouteService
from src.infrastructure.repositories import (
    InMemoryLocationRepository,
    InMemoryHotelRepository,
    InMemoryRouteRepository
)
from src.infrastructure.external_api import MockMappingService


class TestDefects:
    
    def setup_method(self):
        self.location_repo = InMemoryLocationRepository()
        self.hotel_repo = InMemoryHotelRepository()
        self.route_repo = InMemoryRouteRepository()
        self.mapping_service = MockMappingService()
    
    def test_defect_distance_formula(self):
        coords1 = Coordinates(55.7558, 37.6173)
        coords2 = Coordinates(59.9343, 30.3351)
        distance = coords1.distance_to(coords2)
        assert 630 < distance < 640
        print(f"✅ Дефект 1 исправлен: расстояние = {distance:.2f} км")
    
    def test_defect_duration_calculation(self):
        start = Location(name="Start", coordinates=Coordinates(55.7558, 37.6173))
        mid = Location(name="Mid", coordinates=Coordinates(56.8389, 60.6057))
        end = Location(name="End", coordinates=Coordinates(59.9343, 30.3351))
        
        seg1 = RouteSegment(start, mid, TransportType.CAR)
        seg2 = RouteSegment(mid, end, TransportType.CAR)
        route = Route(segments=[seg1, seg2])
        route.calculate_totals()
        
        expected = seg1.duration_min + seg2.duration_min
        assert route.total_duration == expected
        print(f"✅ Дефект 3 исправлен: total_duration = {route.total_duration} мин")
    
    def test_defect_waypoints_handling(self):
        start = Location(name="Start", coordinates=Coordinates(55.7558, 37.6173))
        end = Location(name="End", coordinates=Coordinates(59.9343, 30.3351))
        start = self.location_repo.save(start)
        end = self.location_repo.save(end)
        
        service = RouteService(self.route_repo, self.location_repo, self.hotel_repo)
        route = service.calculate_optimal_route(start.id, end.id, [])
        assert len(route.segments) == 1
        print("✅ Дефект 4 исправлен")
    
    def test_defect_travel_time_calculation(self):
        service = MockMappingService()
        start = Location(name="Start", coordinates=Coordinates(55.7558, 37.6173))
        end = Location(name="End", coordinates=Coordinates(59.9343, 30.3351))
        
        details = service.get_route_details(start, end)
        assert details['duration_min'] > 0
        print(f"✅ Дефект 7 исправлен: время = {details['duration_min']} мин")