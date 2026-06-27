"""
REST API для логистики
"""
from typing import List, Optional
from datetime import datetime
from flask import Flask, request, jsonify

from src.application.services import (
    RouteService, HotelLocationService, RouteOptimizationService
)
from src.application.dto import (
    RouteDTO, RouteSegmentDTO, HotelDTO, 
    RouteOptimizationRequest, CoordinatesDTO
)
from src.core.exceptions import ValidationError, NotFoundError
from src.infrastructure.repositories import (
    InMemoryLocationRepository,
    InMemoryHotelRepository,
    InMemoryRouteRepository
)
from src.infrastructure.external_api import MockMappingService


app = Flask(__name__)

# Инициализация зависимостей
location_repo = InMemoryLocationRepository()
hotel_repo = InMemoryHotelRepository()
route_repo = InMemoryRouteRepository()
mapping_service = MockMappingService()

route_service = RouteService(route_repo, location_repo, hotel_repo)
hotel_service = HotelLocationService(hotel_repo, location_repo)
optimization_service = RouteOptimizationService(
    location_repo, hotel_repo, mapping_service
)


@app.route('/api/routes', methods=['POST'])
def create_route():
    """Создать маршрут"""
    try:
        data = request.json
        route_dto = RouteDTO(
            segments=[
                RouteSegmentDTO(
                    start_location_id=seg['start_location_id'],
                    end_location_id=seg['end_location_id'],
                    transport_type=seg['transport_type']
                )
                for seg in data.get('segments', [])
            ]
        )
        
        route = route_service.create_route_from_dto(route_dto)
        return jsonify({
            'id': route.id,
            'total_distance': route.total_distance,
            'total_duration': route.total_duration,
            'segments': [
                {
                    'start': seg.start.name,
                    'end': seg.end.name,
                    'distance': seg.distance_km,
                    'duration': seg.duration_min
                }
                for seg in route.segments
            ]
        }), 201
    except ValidationError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/routes/<int:route_id>', methods=['GET'])
def get_route(route_id: int):
    """Получить маршрут по ID"""
    try:
        route = route_service.get_route_by_id(route_id)
        return jsonify({
            'id': route.id,
            'total_distance': route.total_distance,
            'total_duration': route.total_duration,
            'created_at': route.created_at.isoformat(),
            'segments': [
                {
                    'start': seg.start.name,
                    'end': seg.end.name,
                    'distance': seg.distance_km,
                    'duration': seg.duration_min,
                    'transport': seg.transport_type.value
                }
                for seg in route.segments
            ]
        })
    except NotFoundError as e:
        return jsonify({'error': str(e)}), 404


@app.route('/api/routes/optimize', methods=['POST'])
def optimize_route():
    """Оптимизировать маршрут"""
    try:
        data = request.json
        request_dto = RouteOptimizationRequest(
            start_location_id=data['start_location_id'],
            end_location_id=data['end_location_id'],
            hotel_ids=data.get('hotel_ids', []),
            transport_type=data.get('transport_type', 'car')
        )
        
        route = optimization_service.optimize_route(request_dto)
        return jsonify({
            'id': route.id,
            'total_distance': route.total_distance,
            'total_duration': route.total_duration,
            'segments': [
                {
                    'start': seg.start.name,
                    'end': seg.end.name,
                    'distance': seg.distance_km,
                    'duration': seg.duration_min
                }
                for seg in route.segments
            ]
        }), 201
    except ValidationError as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/hotels/nearby/<int:location_id>', methods=['GET'])
def get_nearby_hotels(location_id: int):
    """Получить отели рядом с локацией"""
    radius = request.args.get('radius', 10, type=float)
    hotels = hotel_service.get_nearby_hotels(location_id, radius)
    return jsonify([
        {
            'id': h.id,
            'name': h.name,
            'rating': h.rating,
            'price_per_night': h.price_per_night,
            'available_rooms': h.available_rooms,
            'distance': h.location.coordinates.distance_to(
                location_repo.get_by_id(location_id).coordinates
            ) if h.location and h.location.coordinates else None
        }
        for h in hotels
    ])


@app.route('/api/hotels/nearest/<int:location_id>', methods=['GET'])
def get_nearest_hotel(location_id: int):
    """Получить ближайший отель"""
    hotel = hotel_service.find_nearest_hotel(location_id)
    if not hotel:
        return jsonify({'error': 'No hotels found'}), 404
    
    return jsonify({
        'id': hotel.id,
        'name': hotel.name,
        'rating': hotel.rating,
        'price_per_night': hotel.price_per_night,
        'available_rooms': hotel.available_rooms
    })


if __name__ == '__main__':
    app.run(debug=True, port=5000)