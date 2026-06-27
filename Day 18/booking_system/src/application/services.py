from typing import Optional, List
from datetime import datetime
import math

from src.core.domain import (
    Route, RouteSegment, Location, Hotel, Coordinates,
    TransportType, RouteSegment
)
from src.core.exceptions import (
    RouteNotFoundError, HotelNotFoundError, 
    ValidationError, CalculationError, ZeroSpeedError
)
from src.application.dto import (
    RouteDTO, RouteSegmentDTO, HotelDTO, LocationDTO,
    RouteOptimizationRequest, CoordinatesDTO
)
from src.application.interfaces import (
    ILocationRepository, IHotelRepository, IRouteRepository,
    IRouteOptimizationService, IExternalMappingService
)


class RouteService:
    
    def __init__(
        self,
        route_repository: IRouteRepository,
        location_repository: ILocationRepository,
        hotel_repository: IHotelRepository
    ):
        self.route_repository = route_repository
        self.location_repository = location_repository
        self.hotel_repository = hotel_repository
    
    def create_route_from_dto(self, route_dto: RouteDTO) -> Route:
        segments = []
        
        for seg_dto in route_dto.segments:
            start = self.location_repository.get_by_id(seg_dto.start_location_id)
            end = self.location_repository.get_by_id(seg_dto.end_location_id)
            
            if not start or not end:
                raise ValidationError("Start or end location not found")
            
            try:
                transport_type = TransportType(seg_dto.transport_type)
            except ValueError:
                raise ValidationError(f"Invalid transport type: {seg_dto.transport_type}")
            
            segment = RouteSegment(
                start=start,
                end=end,
                transport_type=transport_type,
                distance_km=seg_dto.distance_km or 0,
                duration_min=seg_dto.duration_min or 0
            )
            segments.append(segment)
        
        route = Route(segments=segments)
        route.calculate_totals()
        return self.route_repository.save(route)
    
    def get_route_by_id(self, route_id: int) -> Optional[Route]:
        route = self.route_repository.get_by_id(route_id)
        if not route:
            raise RouteNotFoundError(f"Route with id {route_id} not found")
        return route
    
    def calculate_optimal_route(
        self,
        start_id: int,
        end_id: int,
        waypoint_ids: List[int]
    ) -> Route:
        start = self.location_repository.get_by_id(start_id)
        end = self.location_repository.get_by_id(end_id)
        
        if not start or not end:
            raise ValidationError("Start or end location not found")
        
        waypoints = []
        for wp_id in waypoint_ids:
            wp = self.location_repository.get_by_id(wp_id)
            if wp:
                waypoints.append(wp)
        
        segments = []
        current = start
        
        for waypoint in waypoints:
            segment = RouteSegment(
                start=current,
                end=waypoint,
                transport_type=TransportType.CAR
            )
            segments.append(segment)
            current = waypoint
        
        if current != end:
            final_segment = RouteSegment(
                start=current,
                end=end,
                transport_type=TransportType.CAR
            )
            segments.append(final_segment)
        
        route = Route(segments=segments)
        route.calculate_totals()
        return self.route_repository.save(route)


class HotelLocationService:
    
    def __init__(
        self,
        hotel_repository: IHotelRepository,
        location_repository: ILocationRepository
    ):
        self.hotel_repository = hotel_repository
        self.location_repository = location_repository
    
    def find_nearest_hotel(self, location_id: int) -> Optional[Hotel]:
        location = self.location_repository.get_by_id(location_id)
        if not location or not location.coordinates:
            return None
        
        hotels = self.hotel_repository.get_by_location(location_id, 100)
        
        if not hotels:
            return None
        
        nearest = None
        min_distance = float('inf')
        
        for hotel in hotels:
            if hotel.location and hotel.location.coordinates:
                dist = location.coordinates.distance_to(hotel.location.coordinates)
                if dist < min_distance:
                    min_distance = dist
                    nearest = hotel
        
        return nearest
    
    def get_nearby_hotels(self, location_id: int, radius_km: float) -> List[Hotel]:
        return self.hotel_repository.get_by_location(location_id, radius_km)


class RouteOptimizationService(IRouteOptimizationService):
    
    def __init__(
        self,
        location_repository: ILocationRepository,
        hotel_repository: IHotelRepository,
        mapping_service: IExternalMappingService
    ):
        self.location_repository = location_repository
        self.hotel_repository = hotel_repository
        self.mapping_service = mapping_service
    
    def optimize_route(self, request: RouteOptimizationRequest) -> Route:
        start = self.location_repository.get_by_id(request.start_location_id)
        end = self.location_repository.get_by_id(request.end_location_id)
        
        if not start or not end:
            raise ValidationError("Start or end location not found")
        
        hotels = []
        for hotel_id in request.hotel_ids:
            hotel = self.hotel_repository.get_by_id(hotel_id)
            if hotel:
                hotels.append(hotel)
        
        if not hotels:
            raise ValidationError("No hotels found")
        
        route_points = [start]
        current = start
        visited = set()
        
        for _ in range(len(hotels)):
            nearest = None
            min_dist = float('inf')
            
            for h in hotels:
                if h.id in visited:
                    continue
                if h.location and h.location.coordinates and current.coordinates:
                    dist = current.coordinates.distance_to(h.location.coordinates)
                    if dist < min_dist:
                        min_dist = dist
                        nearest = h
            
            if nearest:
                route_points.append(nearest)
                visited.add(nearest.id)
                current = nearest.location if nearest.location else current
        
        route_points.append(end)
        
        segments = []
        for i in range(len(route_points) - 1):
            start_point = route_points[i]
            end_point = route_points[i+1]
            
            if isinstance(start_point, Hotel):
                start_loc = start_point.location
            else:
                start_loc = start_point
            
            if isinstance(end_point, Hotel):
                end_loc = end_point.location
            else:
                end_loc = end_point
            
            if start_loc and end_loc:
                segment = RouteSegment(
                    start=start_loc,
                    end=end_loc,
                    transport_type=TransportType(request.transport_type)
                )
                segments.append(segment)
        
        route = Route(segments=segments)
        route.calculate_totals()
        return route