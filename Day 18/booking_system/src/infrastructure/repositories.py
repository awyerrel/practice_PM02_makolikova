"""
Реализация репозиториев (in-memory)
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
import math

from src.core.domain import Location, Hotel, Route, RouteSegment, Coordinates
from src.application.interfaces import (
    ILocationRepository, IHotelRepository, IRouteRepository
)
from src.core.exceptions import NotFoundError, ValidationError


class InMemoryLocationRepository(ILocationRepository):
    """In-memory репозиторий для локаций"""
    
    def __init__(self):
        self._locations: Dict[int, Location] = {}
        self._next_id = 1
    
    def get_by_id(self, location_id: int) -> Optional[Location]:
        return self._locations.get(location_id)
    
    def get_by_coordinates(self, lat: float, lon: float, radius_km: float) -> List[Location]:
        point = Coordinates(lat, lon)
        result = []
        
        for location in self._locations.values():
            if location.coordinates:
                dist = point.distance_to(location.coordinates)
                if dist <= radius_km:
                    result.append(location)
        
        return result
    
    def save(self, location: Location) -> Location:
        if not location.id:
            location.id = self._next_id
            self._next_id += 1
        
        self._locations[location.id] = location
        return location


class InMemoryHotelRepository(IHotelRepository):
    """In-memory репозиторий для отелей"""
    
    def __init__(self):
        self._hotels: Dict[int, Hotel] = {}
        self._next_id = 1
    
    def get_by_id(self, hotel_id: int) -> Optional[Hotel]:
        return self._hotels.get(hotel_id)
    
    def get_by_location(self, location_id: int, radius_km: float) -> List[Hotel]:
        location_repo = InMemoryLocationRepository()  # В реальном проекте через DI
        location = location_repo.get_by_id(location_id)
        
        if not location or not location.coordinates:
            return []
        
        result = []
        for hotel in self._hotels.values():
            if hotel.location and hotel.location.coordinates:
                dist = location.coordinates.distance_to(hotel.location.coordinates)
                if dist <= radius_km:
                    result.append(hotel)
        
        return result
    
    def get_by_rating(self, min_rating: float) -> List[Hotel]:
        return [h for h in self._hotels.values() if h.rating >= min_rating]
    
    def save(self, hotel: Hotel) -> Hotel:
        if not hotel.id:
            hotel.id = self._next_id
            self._next_id += 1
        
        self._hotels[hotel.id] = hotel
        return hotel


class InMemoryRouteRepository(IRouteRepository):
    """In-memory репозиторий для маршрутов"""
    
    def __init__(self):
        self._routes: Dict[int, Route] = {}
        self._next_id = 1
    
    def get_by_id(self, route_id: int) -> Optional[Route]:
        return self._routes.get(route_id)
    
    def get_by_locations(self, start_id: int, end_id: int) -> List[Route]:
        result = []
        for route in self._routes.values():
            if not route.segments:
                continue
            
            first_seg = route.segments[0]
            last_seg = route.segments[-1]
            
            if (first_seg.start.id == start_id and last_seg.end.id == end_id):
                result.append(route)
        
        return result
    
    def save(self, route: Route) -> Route:
        if not route.id:
            route.id = self._next_id
            self._next_id += 1
        
        route.updated_at = datetime.now()
        self._routes[route.id] = route
        return route