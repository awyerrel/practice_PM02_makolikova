"""
Тесты для внешних API
"""
import pytest
from unittest.mock import Mock, patch
import time

from src.infrastructure.external_api import MockMappingService
from src.core.domain import Location, Coordinates


class TestMockMappingService:
    """Тесты для MockMappingService"""
    
    def setup_method(self):
        """Подготовка перед каждым тестом"""
        self.service = MockMappingService(simulate_errors=False)
        
        self.start = Location(
            name="Moscow",
            coordinates=Coordinates(55.7558, 37.6173)
        )
        self.end = Location(
            name="Saint Petersburg",
            coordinates=Coordinates(59.9343, 30.3351)
        )
    
    def test_get_route_details(self):
        """Получение деталей маршрута"""
        details = self.service.get_route_details(self.start, self.end)
        
        assert 'distance_km' in details
        assert 'duration_min' in details
        assert 'polyline' in details
        assert 'traffic_level' in details
        assert details['distance_km'] > 0
    
    def test_get_route_details_invalid_coordinates(self):
        """Получение деталей с невалидными координатами"""
        start = Location(name="Invalid")
        end = Location(name="Invalid")
        
        details = self.service.get_route_details(start, end)
        
        assert details['distance_km'] == 0
        assert details['duration_min'] == 0
        assert 'error' in details
    
    def test_get_nearby_hotels(self):
        """Получение отелей рядом"""
        hotels = self.service.get_nearby_hotels(self.start, 10)
        
        assert len(hotels) == 5
        for hotel in hotels:
            assert hotel.id is not None
            assert hotel.name.startswith("Mock Hotel")
            assert hotel.location is not None
    
    @patch('time.sleep')
    def test_get_nearby_hotels_with_simulated_errors(self, mock_sleep):
        """Получение отелей с симуляцией ошибок"""
        service = MockMappingService(simulate_errors=True)
        hotels = service.get_nearby_hotels(self.start, 10)
        
        mock_sleep.assert_called_once_with(2)
        assert len(hotels) == 5
    
    def test_get_route_details_with_errors(self):
        """ОШИБКА 6: Тест должен обнаружить ошибку API"""
        service = MockMappingService(simulate_errors=True)
        
        # ОШИБКА 6: сервис выбрасывает общее исключение при ошибке API
        # Должно быть специальное исключение
        with pytest.raises(Exception):
            service.get_route_details(self.start, self.end)