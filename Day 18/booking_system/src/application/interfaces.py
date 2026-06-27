# src/application/interfaces.py
"""
Интерфейсы для портов и адаптеров
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime

from src.core.domain import Route, Hotel, Location, RouteSegment
from src.application.dto import RouteDTO, HotelDTO, RouteOptimizationRequest


class ILocationRepository(ABC):
    """Репозиторий для локаций"""
    
    @abstractmethod
    def get_by_id(self, location_id: int) -> Optional[Location]:
        pass
    
    @abstractmethod
    def get_by_coordinates(self, lat: float, lon: float, radius_km: float) -> List[Location]:
        pass
    
    @abstractmethod
    def save(self, location: Location) -> Location:
        pass


class IHotelRepository(ABC):
    """Репозиторий для отелей"""
    
    @abstractmethod
    def get_by_id(self, hotel_id: int) -> Optional[Hotel]:
        pass
    
    @abstractmethod
    def get_by_location(self, location_id: int, radius_km: float) -> List[Hotel]:
        pass
    
    @abstractmethod
    def get_by_rating(self, min_rating: float) -> List[Hotel]:
        pass
    
    @abstractmethod
    def save(self, hotel: Hotel) -> Hotel:
        pass


class IRouteRepository(ABC):
    """Репозиторий для маршрутов"""
    
    @abstractmethod
    def get_by_id(self, route_id: int) -> Optional[Route]:
        pass
    
    @abstractmethod
    def get_by_locations(self, start_id: int, end_id: int) -> List[Route]:
        pass
    
    @abstractmethod
    def save(self, route: Route) -> Route:
        pass


class IRouteOptimizationService(ABC):
    """Сервис оптимизации маршрутов"""
    
    @abstractmethod
    def optimize_route(self, request: RouteOptimizationRequest) -> Route:
        """Оптимизировать маршрут с посещением отелей"""
        pass


class IExternalMappingService(ABC):
    """Внешний сервис карт"""
    
    @abstractmethod
    def get_route_details(self, start: Location, end: Location) -> Dict[str, Any]:
        """Получить детали маршрута от внешнего сервиса"""
        pass
    
    @abstractmethod
    def get_nearby_hotels(self, location: Location, radius_km: float) -> List[Hotel]:
        """Получить отели рядом с локацией"""
        pass