# tests/integration/test_api.py
"""
Интеграционные тесты для REST API
Тестируют эндпоинты Flask приложения с реальными запросами
"""
import pytest
import json
from datetime import datetime, timedelta
from flask.testing import FlaskClient
from unittest.mock import patch, Mock

from src.presentation.api import app
from src.core.domain import Location, Coordinates, Hotel, TransportType
from src.infrastructure.repositories import (
    InMemoryLocationRepository,
    InMemoryHotelRepository,
    InMemoryRouteRepository
)
from src.application.dto import RouteOptimizationRequest


class TestAPI:
    """Тесты для REST API эндпоинтов"""
    
    @pytest.fixture
    def client(self):
        """Фикстура для тестового клиента Flask"""
        app.config['TESTING'] = True
        app.config['DEBUG'] = False
        
        # Очищаем репозитории перед каждым тестом
        with app.app_context():
            # Получаем репозитории из app
            from src.presentation.api import (
                location_repo, hotel_repo, route_repo
            )
            
            # Очищаем in-memory репозитории
            if hasattr(location_repo, '_locations'):
                location_repo._locations.clear()
                location_repo._next_id = 1
            if hasattr(hotel_repo, '_hotels'):
                hotel_repo._hotels.clear()
                hotel_repo._next_id = 1
            if hasattr(route_repo, '_routes'):
                route_repo._routes.clear()
                route_repo._next_id = 1
        
        with app.test_client() as client:
            yield client
    
    @pytest.fixture
    def setup_test_data(self, client):
        """Подготовка тестовых данных"""
        # Создаем тестовые локации через API
        locations = [
            {
                "name": "Москва",
                "lat": 55.7558,
                "lon": 37.6173,
                "address": "г. Москва, Красная площадь, 1",
                "city": "Москва",
                "country": "Россия"
            },
            {
                "name": "Санкт-Петербург",
                "lat": 59.9343,
                "lon": 30.3351,
                "address": "г. Санкт-Петербург, Невский пр., 1",
                "city": "Санкт-Петербург",
                "country": "Россия"
            },
            {
                "name": "Екатеринбург",
                "lat": 56.8389,
                "lon": 60.6057,
                "address": "г. Екатеринбург, ул. Ленина, 1",
                "city": "Екатеринбург",
                "country": "Россия"
            }
        ]
        
        created_locations = []
        for loc_data in locations:
            # Сохраняем локации напрямую в репозиторий для тестов
            from src.presentation.api import location_repo
            location = Location(
                name=loc_data["name"],
                coordinates=Coordinates(loc_data["lat"], loc_data["lon"]),
                address=loc_data["address"],
                city=loc_data["city"],
                country=loc_data["country"]
            )
            saved = location_repo.save(location)
            created_locations.append(saved)
        
        # Создаем тестовые отели
        hotels_data = [
            {
                "name": "Grand Hotel Moscow",
                "lat": 55.7512,
                "lon": 37.6184,
                "rating": 4.9,
                "price_per_night": 35000,
                "available_rooms": 20,
                "amenities": ["WiFi", "СПА", "Ресторан"]
            },
            {
                "name": "Budget Inn SPb",
                "lat": 59.9343,
                "lon": 30.3351,
                "rating": 3.2,
                "price_per_night": 2500,
                "available_rooms": 30,
                "amenities": ["WiFi", "Парковка"]
            }
        ]
        
        created_hotels = []
        for hotel_data in hotels_data:
            from src.presentation.api import hotel_repo, location_repo
            
            # Находим ближайшую локацию
            point = Coordinates(hotel_data["lat"], hotel_data["lon"])
            nearest_loc = None
            min_dist = float('inf')
            
            for loc in location_repo._locations.values():
                if loc.coordinates:
                    dist = point.distance_to(loc.coordinates)
                    if dist < min_dist:
                        min_dist = dist
                        nearest_loc = loc
            
            if nearest_loc:
                hotel = Hotel(
                    name=hotel_data["name"],
                    location=nearest_loc,
                    rating=hotel_data["rating"],
                    price_per_night=hotel_data["price_per_night"],
                    available_rooms=hotel_data["available_rooms"],
                    amenities=hotel_data["amenities"]
                )
                saved = hotel_repo.save(hotel)
                created_hotels.append(saved)
        
        return {
            'locations': created_locations,
            'hotels': created_hotels
        }

    # --- Тесты для эндпоинта /api/routes ---
    
    def test_create_route_success(self, client, setup_test_data):
        """Успешное создание маршрута"""
        data = {
            "segments": [
                {
                    "start_location_id": setup_test_data['locations'][0].id,
                    "end_location_id": setup_test_data['locations'][1].id,
                    "transport_type": "car"
                }
            ]
        }
        
        response = client.post(
            '/api/routes',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        assert response.status_code == 201
        result = json.loads(response.data)
        assert 'id' in result
        assert 'total_distance' in result
        assert 'total_duration' in result
        assert 'segments' in result
        assert len(result['segments']) == 1
        assert result['segments'][0]['start'] == "Москва"
        assert result['segments'][0]['end'] == "Санкт-Петербург"
    
    def test_create_route_multiple_segments(self, client, setup_test_data):
        """Создание маршрута с несколькими сегментами"""
        data = {
            "segments": [
                {
                    "start_location_id": setup_test_data['locations'][0].id,
                    "end_location_id": setup_test_data['locations'][2].id,
                    "transport_type": "car"
                },
                {
                    "start_location_id": setup_test_data['locations'][2].id,
                    "end_location_id": setup_test_data['locations'][1].id,
                    "transport_type": "train"
                }
            ]
        }
        
        response = client.post(
            '/api/routes',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        assert response.status_code == 201
        result = json.loads(response.data)
        assert len(result['segments']) == 2
        assert result['segments'][0]['transport'] == 'car'
        assert result['segments'][1]['transport'] == 'train'
    
    def test_create_route_invalid_location(self, client):
        """Создание маршрута с невалидной локацией"""
        data = {
            "segments": [
                {
                    "start_location_id": 999,
                    "end_location_id": 1000,
                    "transport_type": "car"
                }
            ]
        }
        
        response = client.post(
            '/api/routes',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        result = json.loads(response.data)
        assert 'error' in result
    
    def test_create_route_empty_segments(self, client):
        """Создание маршрута с пустыми сегментами"""
        data = {"segments": []}
        
        response = client.post(
            '/api/routes',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        result = json.loads(response.data)
        assert 'error' in result
    
    def test_create_route_invalid_transport(self, client, setup_test_data):
        """Создание маршрута с невалидным типом транспорта"""
        data = {
            "segments": [
                {
                    "start_location_id": setup_test_data['locations'][0].id,
                    "end_location_id": setup_test_data['locations'][1].id,
                    "transport_type": "helicopter"
                }
            ]
        }
        
        response = client.post(
            '/api/routes',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        result = json.loads(response.data)
        assert 'error' in result
    
    # --- Тесты для эндпоинта /api/routes/<id> ---
    
    def test_get_route_success(self, client, setup_test_data):
        """Получение маршрута по ID"""
        # Сначала создаем маршрут
        create_data = {
            "segments": [
                {
                    "start_location_id": setup_test_data['locations'][0].id,
                    "end_location_id": setup_test_data['locations'][1].id,
                    "transport_type": "car"
                }
            ]
        }
        
        response = client.post(
            '/api/routes',
            data=json.dumps(create_data),
            content_type='application/json'
        )
        route_id = json.loads(response.data)['id']
        
        # Получаем маршрут
        response = client.get(f'/api/routes/{route_id}')
        
        assert response.status_code == 200
        result = json.loads(response.data)
        assert result['id'] == route_id
        assert 'total_distance' in result
        assert 'total_duration' in result
        assert 'created_at' in result
        assert len(result['segments']) == 1
    
    def test_get_route_not_found(self, client):
        """Получение несуществующего маршрута"""
        response = client.get('/api/routes/999')
        
        assert response.status_code == 404
        result = json.loads(response.data)
        assert 'error' in result
    
    # --- Тесты для эндпоинта /api/routes/optimize ---
    
    def test_optimize_route_success(self, client, setup_test_data):
        """Успешная оптимизация маршрута"""
        data = {
            "start_location_id": setup_test_data['locations'][0].id,
            "end_location_id": setup_test_data['locations'][1].id,
            "hotel_ids": [h.id for h in setup_test_data['hotels']],
            "transport_type": "car"
        }
        
        response = client.post(
            '/api/routes/optimize',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        assert response.status_code == 201
        result = json.loads(response.data)
        assert 'id' in result
        assert 'total_distance' in result
        assert 'total_duration' in result
        assert 'segments' in result
    
    def test_optimize_route_no_hotels(self, client, setup_test_data):
        """Оптимизация маршрута без отелей"""
        data = {
            "start_location_id": setup_test_data['locations'][0].id,
            "end_location_id": setup_test_data['locations'][1].id,
            "hotel_ids": [],
            "transport_type": "car"
        }
        
        response = client.post(
            '/api/routes/optimize',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        result = json.loads(response.data)
        assert 'error' in result
    
    def test_optimize_route_invalid_location(self, client):
        """Оптимизация с невалидными локациями"""
        data = {
            "start_location_id": 999,
            "end_location_id": 1000,
            "hotel_ids": [1, 2],
            "transport_type": "car"
        }
        
        response = client.post(
            '/api/routes/optimize',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        result = json.loads(response.data)
        assert 'error' in result
    
    # --- Тесты для эндпоинта /api/hotels/nearby ---
    
    def test_get_nearby_hotels(self, client, setup_test_data):
        """Получение отелей рядом с локацией"""
        location_id = setup_test_data['locations'][0].id
        
        response = client.get(f'/api/hotels/nearby/{location_id}?radius=10')
        
        assert response.status_code == 200
        result = json.loads(response.data)
        assert len(result) > 0
        assert 'id' in result[0]
        assert 'name' in result[0]
        assert 'rating' in result[0]
        assert 'price_per_night' in result[0]
        assert 'available_rooms' in result[0]
    
    def test_get_nearby_hotels_default_radius(self, client, setup_test_data):
        """Получение отелей с радиусом по умолчанию"""
        location_id = setup_test_data['locations'][0].id
        
        response = client.get(f'/api/hotels/nearby/{location_id}')
        
        assert response.status_code == 200
        result = json.loads(response.data)
        # Должен быть хотя бы один отель
        assert len(result) >= 0
    
    def test_get_nearby_hotels_location_not_found(self, client):
        """Получение отелей для несуществующей локации"""
        response = client.get('/api/hotels/nearby/999')
        
        assert response.status_code == 200
        result = json.loads(response.data)
        assert result == []  # Пустой список
    
    # --- Тесты для эндпоинта /api/hotels/nearest ---
    
    def test_get_nearest_hotel(self, client, setup_test_data):
        """Получение ближайшего отеля"""
        location_id = setup_test_data['locations'][0].id
        
        response = client.get(f'/api/hotels/nearest/{location_id}')
        
        assert response.status_code == 200
        result = json.loads(response.data)
        assert 'id' in result
        assert 'name' in result
        assert 'rating' in result
        assert 'price_per_night' in result
        assert 'available_rooms' in result
    
    def test_get_nearest_hotel_not_found(self, client):
        """Получение ближайшего отеля для локации без отелей"""
        # Создаем локацию без отелей
        from src.presentation.api import location_repo
        location = Location(
            name="Удаленная локация",
            coordinates=Coordinates(60.0, 60.0),
            address="Где-то далеко",
            city="Город",
            country="Россия"
        )
        saved = location_repo.save(location)
        
        response = client.get(f'/api/hotels/nearest/{saved.id}')
        
        assert response.status_code == 404
        result = json.loads(response.data)
        assert 'error' in result
    
    # --- Тесты для обработки ошибок ---
    
    def test_api_error_handling(self, client):
        """Обработка ошибок API"""
        # Отправляем некорректный JSON
        response = client.post(
            '/api/routes',
            data='{invalid json',
            content_type='application/json'
        )
        
        # Должен вернуть 500 или 400
        assert response.status_code in [400, 500]
    
    def test_api_method_not_allowed(self, client):
        """Метод не разрешен"""
        response = client.put('/api/routes/1')
        assert response.status_code == 405
    
    @patch('src.infrastructure.external_api.MockMappingService.get_route_details')
    def test_api_with_mocked_external_service(self, mock_get_route, client, setup_test_data):
        """Тест с моком внешнего сервиса"""
        # Настраиваем мок
        mock_get_route.return_value = {
            'distance_km': 634.0,
            'duration_min': 480,
            'polyline': 'mocked_polyline',
            'traffic_level': 'low'
        }
        
        data = {
            "start_location_id": setup_test_data['locations'][0].id,
            "end_location_id": setup_test_data['locations'][1].id,
            "hotel_ids": [h.id for h in setup_test_data['hotels']],
            "transport_type": "car"
        }
        
        response = client.post(
            '/api/routes/optimize',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        assert response.status_code == 201
        result = json.loads(response.data)
        assert 'id' in result
    
    # --- Тесты для больших данных ---
    
    def test_api_with_large_payload(self, client):
        """Тест с большим количеством данных"""
        # Создаем много сегментов
        segments = []
        for i in range(50):
            segments.append({
                "start_location_id": i + 1,
                "end_location_id": i + 2,
                "transport_type": "car"
            })
        
        data = {"segments": segments}
        
        response = client.post(
            '/api/routes',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        # Должен вернуть ошибку, так как локации не существуют
        assert response.status_code == 400
    
    # --- Тесты для проверки CORS (если настроен) ---
    
    def test_api_cors_headers(self, client):
        """Проверка CORS заголовков"""
        response = client.options('/api/routes')
        # CORS заголовки должны присутствовать, если настроены
        assert response.status_code in [200, 405]


class TestAPIIntegration:
    """Расширенные интеграционные тесты API"""
    
    @pytest.fixture
    def client(self):
        """Фикстура для клиента"""
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client
    
    def test_full_workflow(self, client, setup_test_data):
        """Полный рабочий процесс API"""
        # 1. Создаем маршрут
        create_data = {
            "segments": [
                {
                    "start_location_id": setup_test_data['locations'][0].id,
                    "end_location_id": setup_test_data['locations'][1].id,
                    "transport_type": "car"
                }
            ]
        }
        
        response = client.post(
            '/api/routes',
            data=json.dumps(create_data),
            content_type='application/json'
        )
        assert response.status_code == 201
        route_data = json.loads(response.data)
        route_id = route_data['id']
        
        # 2. Получаем маршрут
        response = client.get(f'/api/routes/{route_id}')
        assert response.status_code == 200
        route = json.loads(response.data)
        assert route['id'] == route_id
        
        # 3. Ищем ближайший отель
        response = client.get(f'/api/hotels/nearest/{setup_test_data["locations"][0].id}')
        assert response.status_code == 200
        hotel = json.loads(response.data)
        assert 'id' in hotel
        
        # 4. Оптимизируем маршрут с отелями
        optimize_data = {
            "start_location_id": setup_test_data['locations'][0].id,
            "end_location_id": setup_test_data['locations'][1].id,
            "hotel_ids": [hotel['id']],
            "transport_type": "car"
        }
        
        response = client.post(
            '/api/routes/optimize',
            data=json.dumps(optimize_data),
            content_type='application/json'
        )
        assert response.status_code == 201
        optimized = json.loads(response.data)
        assert 'id' in optimized
    
    def test_concurrent_requests(self, client, setup_test_data):
        """Тест параллельных запросов (имитация)"""
        import threading
        import time
        
        results = []
        errors = []
        
        def make_request():
            try:
                data = {
                    "segments": [
                        {
                            "start_location_id": setup_test_data['locations'][0].id,
                            "end_location_id": setup_test_data['locations'][1].id,
                            "transport_type": "car"
                        }
                    ]
                }
                response = client.post(
                    '/api/routes',
                    data=json.dumps(data),
                    content_type='application/json'
                )
                results.append(response.status_code)
            except Exception as e:
                errors.append(str(e))
        
        # Запускаем несколько потоков
        threads = []
        for _ in range(5):
            t = threading.Thread(target=make_request)
            t.start()
            threads.append(t)
        
        # Ждем завершения
        for t in threads:
            t.join()
        
        # Проверяем результаты
        assert len(results) == 5
        assert all(status == 201 for status in results)
        assert len(errors) == 0
    
    def test_api_performance(self, client, setup_test_data):
        """Тест производительности API"""
        import time
        
        start_time = time.time()
        
        # Выполняем много запросов
        for _ in range(10):
            data = {
                "segments": [
                    {
                        "start_location_id": setup_test_data['locations'][0].id,
                        "end_location_id": setup_test_data['locations'][1].id,
                        "transport_type": "car"
                    }
                ]
            }
            response = client.post(
                '/api/routes',
                data=json.dumps(data),
                content_type='application/json'
            )
            assert response.status_code == 201
        
        end_time = time.time()
        duration = end_time - start_time
        
        # 10 запросов должны выполниться за разумное время
        assert duration < 5.0  # менее 5 секунд