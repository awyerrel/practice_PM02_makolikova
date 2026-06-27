"""
DTO для передачи данных между слоями
"""
from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime


@dataclass
class CoordinatesDTO:
    """DTO для координат"""
    lat: float
    lon: float


@dataclass
class LocationDTO:
    """DTO для локации"""
    id: Optional[int] = None
    name: str = ""
    coordinates: Optional[CoordinatesDTO] = None
    address: str = ""
    city: str = ""
    country: str = ""


@dataclass
class RouteSegmentDTO:
    """DTO для сегмента маршрута"""
    start_location_id: int
    end_location_id: int
    transport_type: str
    distance_km: Optional[float] = None
    duration_min: Optional[int] = None


@dataclass
class RouteDTO:
    """DTO для маршрута"""
    id: Optional[int] = None
    segments: List[RouteSegmentDTO] = field(default_factory=list)
    total_distance: float = 0.0
    total_duration: int = 0
    departure_time: Optional[datetime] = None


@dataclass
class HotelDTO:
    """DTO для отеля"""
    id: Optional[int] = None
    name: str = ""
    location: Optional[LocationDTO] = None
    rating: float = 0.0
    price_per_night: float = 0.0
    available_rooms: int = 0
    amenities: List[str] = field(default_factory=list)


@dataclass
class RouteOptimizationRequest:
    """Запрос на оптимизацию маршрута"""
    start_location_id: int
    end_location_id: int
    hotel_ids: List[int]
    transport_type: str = "car"