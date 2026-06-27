from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime, timedelta
from enum import Enum
import math

from .exceptions import ValidationError, ZeroSpeedError


class TransportType(Enum):
    CAR = "car"
    BUS = "bus"
    TRAIN = "train"
    PLANE = "plane"
    WALK = "walk"


@dataclass
class Coordinates:
    lat: float
    lon: float
    
    def __post_init__(self):
        if not (-90 <= self.lat <= 90):
            raise ValidationError(f"Invalid latitude: {self.lat}")
        if not (-180 <= self.lon <= 180):
            raise ValidationError(f"Invalid longitude: {self.lon}")
    
    def __hash__(self):
        return hash((self.lat, self.lon))
    
    def distance_to(self, other: 'Coordinates') -> float:
        R = 6371
        lat1 = math.radians(self.lat)
        lat2 = math.radians(other.lat)
        dlat = math.radians(other.lat - self.lat)
        dlon = math.radians(other.lon - self.lon)
        
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c


@dataclass
class Location:
    id: Optional[int] = None
    name: str = ""
    coordinates: Optional[Coordinates] = None
    address: str = ""
    city: str = ""
    country: str = ""
    
    def get_distance_to(self, other: 'Location') -> float:
        if not self.coordinates or not other.coordinates:
            return 0.0
        return self.coordinates.distance_to(other.coordinates)


@dataclass
class RouteSegment:
    start: Location
    end: Location
    transport_type: TransportType
    distance_km: float = 0.0
    duration_min: int = 0
    
    def __post_init__(self):
        if self.distance_km == 0 and self.start.coordinates and self.end.coordinates:
            self.distance_km = self.start.get_distance_to(self.end)
        
        if self.duration_min == 0:
            speed_map = {
                TransportType.CAR: 60,
                TransportType.BUS: 40,
                TransportType.TRAIN: 80,
                TransportType.PLANE: 800,
                TransportType.WALK: 5
            }
            speed_kmh = speed_map.get(self.transport_type, 50)
            
            if speed_kmh <= 0:
                raise ZeroSpeedError(f"Speed cannot be zero for transport type: {self.transport_type}")
            
            self.duration_min = int((self.distance_km / speed_kmh) * 60)


@dataclass
class Route:
    id: Optional[int] = None
    segments: List[RouteSegment] = field(default_factory=list)
    total_distance: float = 0.0
    total_duration: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None
    
    def calculate_totals(self):
        self.total_distance = sum(seg.distance_km for seg in self.segments)
        self.total_duration = sum(seg.duration_min for seg in self.segments)
    
    def add_segment(self, segment: RouteSegment):
        self.segments.append(segment)
        self.calculate_totals()
    
    def get_estimated_arrival(self, departure_time: datetime) -> datetime:
        return departure_time + timedelta(minutes=self.total_duration)


@dataclass
class Hotel:
    id: Optional[int] = None
    name: str = ""
    location: Optional[Location] = None
    rating: float = 0.0
    price_per_night: float = 0.0
    available_rooms: int = 0
    amenities: List[str] = field(default_factory=list)