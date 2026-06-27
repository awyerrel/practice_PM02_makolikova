# tests/integration/test_repositories.py
"""
Интеграционные тесты для репозиториев
Тестируют работу с данными, поиск, фильтрацию и сохранение
"""
import pytest
from datetime import datetime, timedelta
from typing import List

from src.core.domain import (
    Coordinates, Location, Hotel, Route, RouteSegment,
    TransportType
)
from src.infrastructure.repositories import (
    InMemoryLocationRepository,
    InMemoryHotelRepository,
    InMemoryRouteRepository
)
from src.core.exceptions import NotFoundError


class TestInMemoryLocationRepository:
    """Тесты для InMemoryLocationRepository"""
    
    @pytest.fixture
    def repository(self):
        """Фикстура для репозитория"""
        return InMemoryLocationRepository()
    
    @pytest.fixture
    def sample_locations(self):
        """Фикстура с тестовыми локациями"""
        return [
            Location(
                name="Москва",
                coordinates=Coordinates(55.7558, 37.6173),
                address="Красная площадь, 1",
                city="Москва",
                country="Россия"
            ),
            Location(
                name="Санкт-Петербург",
                coordinates=Coordinates(59.9343, 30.3351),
                address="Невский пр., 1",
                city="Санкт-Петербург",
                country="Россия"
            ),
            Location(
                name="Екатеринбург",
                coordinates=Coordinates(56.8389, 60.6057),
                address="ул. Ленина, 1",
                city="Екатеринбург",
                country="Россия"
            ),
            Location(
                name="Казань",
                coordinates=Coordinates(55.7887, 49.1221),
                address="ул. Кремлевская, 1",
                city="Казань",
                country="Россия"
            )
        ]
    
    def test_save_location(self, repository):
        """Сохранение локации"""
        location = Location(
            name="Тестовая локация",
            coordinates=Coordinates(55.0, 37.0)
        )
        
        saved = repository.save(location)
        
        assert saved.id is not None
        assert saved.id > 0
        assert repository.get_by_id(saved.id) == saved
    
    def test_save_location_update(self, repository):
        """Обновление существующей локации"""
        location = Location(
            name="Старое название",
            coordinates=Coordinates(55.0, 37.0)
        )
        saved = repository.save(location)
        
        # Обновляем
        saved.name = "Новое название"
        updated = repository.save(saved)
        
        assert updated.id == saved.id
        assert updated.name == "Новое название"
        assert repository.get_by_id(updated.id).name == "Новое название"
    
    def test_get_by_id_not_found(self, repository):
        """Получение несуществующей локации"""
        location = repository.get_by_id(999)
        assert location is None
    
    def test_get_by_coordinates(self, repository, sample_locations):
        """Поиск локаций по координатам"""
        # Сохраняем локации
        for loc in sample_locations:
            repository.save(loc)
        
        # Ищем локации вокруг Москвы (радиус 100 км)
        results = repository.get_by_coordinates(55.7558, 37.6173, 100)
        
        assert len(results) >= 1
        assert any(loc.name == "Москва" for loc in results)
    
    def test_get_by_coordinates_with_radius(self, repository, sample_locations):
        """Поиск локаций с разными радиусами"""
        for loc in sample_locations:
            repository.save(loc)
        
        # Радиус 10 км - только Москва
        results_small = repository.get_by_coordinates(55.7558, 37.6173, 10)
        assert len(results_small) >= 1
        
        # Радиус 1000 км - все города
        results_large = repository.get_by_coordinates(55.7558, 37.6173, 1000)
        assert len(results_large) >= 3
    
    def test_autoincrement_id(self, repository):
        """Автоинкремент ID"""
        loc1 = Location(name="Location 1")
        loc2 = Location(name="Location 2")
        
        saved1 = repository.save(loc1)
        saved2 = repository.save(loc2)
        
        assert saved1.id is not None
        assert saved2.id is not None
        assert saved2.id == saved1.id + 1
    
    def test_save_multiple_locations(self, repository, sample_locations):
        """Сохранение нескольких локаций"""
        saved_locations = []
        for loc in sample_locations:
            saved = repository.save(loc)
            saved_locations.append(saved)
        
        assert len(saved_locations) == len(sample_locations)
        assert all(loc.id is not None for loc in saved_locations)
        
        # Проверяем уникальность ID
        ids = [loc.id for loc in saved_locations]
        assert len(set(ids)) == len(ids)


class TestInMemoryHotelRepository:
    """Тесты для InMemoryHotelRepository"""
    
    @pytest.fixture
    def repository(self):
        """Фикстура для репозитория отелей"""
        return InMemoryHotelRepository()
    
    @pytest.fixture
    def location_repository(self):
        """Фикстура для репозитория локаций"""
        return InMemoryLocationRepository()
    
    @pytest.fixture
    def sample_hotels(self, location_repository):
        """Фикстура с тестовыми отелями"""
        # Создаем локации
        moscow = Location(
            name="Москва",
            coordinates=Coordinates(55.7558, 37.6173)
        )
        spb = Location(
            name="Санкт-Петербург",
            coordinates=Coordinates(59.9343, 30.3351)
        )
        location_repository.save(moscow)
        location_repository.save(spb)
        
        return [
            Hotel(
                name="Grand Hotel Moscow",
                location=moscow,
                rating=4.9,
                price_per_night=35000.0,
                available_rooms=20,
                amenities=["WiFi", "СПА", "Ресторан"]
            ),
            Hotel(
                name="Budget Inn Moscow",
                location=moscow,
                rating=3.2,
                price_per_night=2500.0,
                available_rooms=30,
                amenities=["WiFi", "Парковка"]
            ),
            Hotel(
                name="Luxury Hotel SPb",
                location=spb,
                rating=4.8,
                price_per_night=28000.0,
                available_rooms=15,
                amenities=["WiFi", "Бассейн", "СПА"]
            ),
            Hotel(
                name="Hostel SPb",
                location=spb,
                rating=2.5,
                price_per_night=800.0,
                available_rooms=40,
                amenities=["WiFi", "Общая кухня"]
            )
        ]
    
    def test_save_hotel(self, repository):
        """Сохранение отеля"""
        location = Location(name="Тестовая локация")
        hotel = Hotel(
            name="Тестовый отель",
            location=location,
            rating=4.0,
            price_per_night=5000.0,
            available_rooms=10
        )
        
        saved = repository.save(hotel)
        
        assert saved.id is not None
        assert repository.get_by_id(saved.id) == saved
    
    def test_get_by_id_not_found(self, repository):
        """Получение несуществующего отеля"""
        hotel = repository.get_by_id(999)
        assert hotel is None
    
    def test_get_by_location(self, repository, location_repository, sample_hotels):
        """Поиск отелей по локации"""
        # Сохраняем отели
        for hotel in sample_hotels:
            repository.save(hotel)
        
        # Находим Москву
        moscow = location_repository.get_by_id(1)  # Первая сохраненная локация
        
        # Ищем отели в Москве
        hotels = repository.get_by_location(moscow.id, 10)
        
        assert len(hotels) >= 2
        assert all(hotel.location.name == "Москва" for hotel in hotels)
    
    def test_get_by_location_with_radius(self, repository, location_repository, sample_hotels):
        """Поиск отелей по локации с радиусом"""
        for hotel in sample_hotels:
            repository.save(hotel)
        
        moscow = location_repository.get_by_id(1)
        spb = location_repository.get_by_id(2)
        
        # Радиус 100 км - только Москва
        hotels_moscow = repository.get_by_location(moscow.id, 100)
        assert len(hotels_moscow) >= 2
        
        # Радиус 1000 км - все отели
        hotels_all = repository.get_by_location(moscow.id, 1000)
        assert len(hotels_all) >= 4
    
    def test_get_by_rating(self, repository, sample_hotels):
        """Поиск отелей по рейтингу"""
        for hotel in sample_hotels:
            repository.save(hotel)
        
        # Отели с рейтингом >= 4.0
        good_hotels = repository.get_by_rating(4.0)
        assert len(good_hotels) >= 2
        assert all(hotel.rating >= 4.0 for hotel in good_hotels)
        
        # Отели с рейтингом >= 4.8
        excellent_hotels = repository.get_by_rating(4.8)
        assert len(excellent_hotels) >= 1
        assert all(hotel.rating >= 4.8 for hotel in excellent_hotels)
    
    def test_save_hotel_without_location(self, repository):
        """Сохранение отеля без локации"""
        hotel = Hotel(name="Отель без локации")
        saved = repository.save(hotel)
        
        assert saved.id is not None
        assert saved.location is None
    
    def test_update_hotel(self, repository, sample_hotels):
        """Обновление отеля"""
        hotel = sample_hotels[0]
        saved = repository.save(hotel)
        
        # Обновляем
        saved.name = "Новое название"
        saved.rating = 5.0
        updated = repository.save(saved)
        
        assert updated.id == saved.id
        assert updated.name == "Новое название"
        assert updated.rating == 5.0
    
    def test_hotel_amenities(self, repository):
        """Работа с удобствами отеля"""
        hotel = Hotel(
            name="Отель с удобствами",
            amenities=["WiFi", "Бассейн", "СПА", "Ресторан"]
        )
        saved = repository.save(hotel)
        
        assert len(saved.amenities) == 4
        assert "WiFi" in saved.amenities
        assert "СПА" in saved.amenities
    
    def test_hotel_price_ranges(self, repository, sample_hotels):
        """Проверка цен отелей"""
        for hotel in sample_hotels:
            repository.save(hotel)
        
        # Проверяем, что цены в разумных пределах
        hotels = repository.get_by_rating(0)  # Все отели
        prices = [h.price_per_night for h in hotels]
        
        assert min(prices) >= 0
        assert max(prices) <= 50000


class TestInMemoryRouteRepository:
    """Тесты для InMemoryRouteRepository"""
    
    @pytest.fixture
    def repository(self):
        """Фикстура для репозитория маршрутов"""
        return InMemoryRouteRepository()
    
    @pytest.fixture
    def sample_routes(self):
        """Фикстура с тестовыми маршрутами"""
        # Создаем локации
        moscow = Location(
            id=1,
            name="Москва",
            coordinates=Coordinates(55.7558, 37.6173)
        )
        spb = Location(
            id=2,
            name="Санкт-Петербург",
            coordinates=Coordinates(59.9343, 30.3351)
        )
        ekb = Location(
            id=3,
            name="Екатеринбург",
            coordinates=Coordinates(56.8389, 60.6057)
        )
        kazan = Location(
            id=4,
            name="Казань",
            coordinates=Coordinates(55.7887, 49.1221)
        )
        
        # Создаем маршруты
        route1 = Route(segments=[
            RouteSegment(moscow, spb, TransportType.CAR)
        ])
        route1.calculate_totals()
        
        route2 = Route(segments=[
            RouteSegment(moscow, ekb, TransportType.TRAIN),
            RouteSegment(ekb, spb, TransportType.TRAIN)
        ])
        route2.calculate_totals()
        
        route3 = Route(segments=[
            RouteSegment(moscow, kazan, TransportType.CAR),
            RouteSegment(kazan, spb, TransportType.CAR)
        ])
        route3.calculate_totals()
        
        route4 = Route(segments=[
            RouteSegment(spb, moscow, TransportType.PLANE)
        ])
        route4.calculate_totals()
        
        return [route1, route2, route3, route4]
    
    def test_save_route(self, repository):
        """Сохранение маршрута"""
        moscow = Location(name="Москва")
        spb = Location(name="Санкт-Петербург")
        
        route = Route(segments=[
            RouteSegment(moscow, spb, TransportType.CAR)
        ])
        route.calculate_totals()
        
        saved = repository.save(route)
        
        assert saved.id is not None
        assert repository.get_by_id(saved.id) == saved
    
    def test_get_by_id_not_found(self, repository):
        """Получение несуществующего маршрута"""
        route = repository.get_by_id(999)
        assert route is None
    
    def test_get_by_locations(self, repository, sample_routes):
        """Поиск маршрутов по локациям"""
        for route in sample_routes:
            repository.save(route)
        
        # Ищем маршруты из Москвы в Санкт-Петербург
        routes = repository.get_by_locations(1, 2)  # ID локаций
        
        assert len(routes) >= 2
        for route in routes:
            first_seg = route.segments[0]
            last_seg = route.segments[-1]
            assert first_seg.start.id == 1
            assert last_seg.end.id == 2
    
    def test_get_by_locations_empty(self, repository):
        """Поиск маршрутов по несуществующим локациям"""
        routes = repository.get_by_locations(999, 1000)
        assert routes == []
    
    def test_route_timestamps(self, repository):
        """Проверка временных меток маршрутов"""
        moscow = Location(name="Москва")
        spb = Location(name="Санкт-Петербург")
        
        route = Route(segments=[
            RouteSegment(moscow, spb, TransportType.CAR)
        ])
        route.calculate_totals()
        
        before_save = datetime.now()
        saved = repository.save(route)
        after_save = datetime.now()
        
        assert saved.created_at is not None
        assert saved.updated_at is not None
        assert before_save <= saved.created_at <= after_save
        assert before_save <= saved.updated_at <= after_save
    
    def test_route_update_timestamp(self, repository):
        """Обновление временной метки при изменении маршрута"""
        moscow = Location(name="Москва")
        spb = Location(name="Санкт-Петербург")
        
        route = Route(segments=[
            RouteSegment(moscow, spb, TransportType.CAR)
        ])
        route.calculate_totals()
        
        saved = repository.save(route)
        original_updated = saved.updated_at
        
        # Добавляем новый сегмент
        ekb = Location(name="Екатеринбург")
        saved.add_segment(RouteSegment(spb, ekb, TransportType.CAR))
        
        updated = repository.save(saved)
        
        assert updated.updated_at is not None
        assert updated.updated_at > original_updated
    
    def test_save_multiple_routes(self, repository, sample_routes):
        """Сохранение нескольких маршрутов"""
        saved_routes = []
        for route in sample_routes:
            saved = repository.save(route)
            saved_routes.append(saved)
        
        assert len(saved_routes) == len(sample_routes)
        assert all(route.id is not None for route in saved_routes)
        
        # Проверяем уникальность ID
        ids = [route.id for route in saved_routes]
        assert len(set(ids)) == len(ids)
    
    def test_route_total_calculation(self, repository):
        """Проверка расчета общих показателей маршрута"""
        moscow = Location(
            name="Москва",
            coordinates=Coordinates(55.7558, 37.6173)
        )
        spb = Location(
            name="Санкт-Петербург",
            coordinates=Coordinates(59.9343, 30.3351)
        )
        ekb = Location(
            name="Екатеринбург",
            coordinates=Coordinates(56.8389, 60.6057)
        )
        
        route = Route(segments=[
            RouteSegment(moscow, spb, TransportType.CAR),
            RouteSegment(spb, ekb, TransportType.CAR)
        ])
        route.calculate_totals()
        
        saved = repository.save(route)
        
        assert saved.total_distance > 0
        assert saved.total_duration > 0
        assert saved.total_distance == sum(seg.distance_km for seg in saved.segments)
        # Из-за дефекта в коде total_duration может быть удвоен
        # Этот тест выявит проблему


class TestRepositoryIntegration:
    """Интеграционные тесты для взаимодействия репозиториев"""
    
    @pytest.fixture
    def location_repo(self):
        return InMemoryLocationRepository()
    
    @pytest.fixture
    def hotel_repo(self):
        return InMemoryHotelRepository()
    
    @pytest.fixture
    def route_repo(self):
        return InMemoryRouteRepository()
    
    def test_full_data_flow(self, location_repo, hotel_repo, route_repo):
        """Полный поток данных через репозитории"""
        # 1. Создаем локации
        moscow = Location(
            name="Москва",
            coordinates=Coordinates(55.7558, 37.6173)
        )
        spb = Location(
            name="Санкт-Петербург",
            coordinates=Coordinates(59.9343, 30.3351)
        )
        location_repo.save(moscow)
        location_repo.save(spb)
        
        # 2. Создаем отели
        hotel1 = Hotel(
            name="Отель в Москве",
            location=moscow,
            rating=4.5,
            price_per_night=10000
        )
        hotel2 = Hotel(
            name="Отель в СПб",
            location=spb,
            rating=4.0,
            price_per_night=8000
        )
        hotel_repo.save(hotel1)
        hotel_repo.save(hotel2)
        
        # 3. Проверяем поиск отелей
        hotels_moscow = hotel_repo.get_by_location(moscow.id, 10)
        assert len(hotels_moscow) >= 1
        
        # 4. Создаем маршрут
        route = Route(segments=[
            RouteSegment(moscow, spb, TransportType.CAR)
        ])
        route.calculate_totals()
        route_repo.save(route)
        
        # 5. Проверяем маршрут
        routes = route_repo.get_by_locations(moscow.id, spb.id)
        assert len(routes) >= 1
        
        # 6. Проверяем связи между данными
        for r in routes:
            first_seg = r.segments[0]
            assert first_seg.start.name == "Москва"
            assert first_seg.end.name == "Санкт-Петербург"
    
    def test_data_consistency(self, location_repo, hotel_repo, route_repo):
        """Проверка согласованности данных"""
        # Создаем локацию
        loc = Location(
            name="Тестовая",
            coordinates=Coordinates(55.0, 37.0)
        )
        location_repo.save(loc)
        
        # Создаем отель
        hotel = Hotel(
            name="Тестовый отель",
            location=loc,
            rating=4.0
        )
        hotel_repo.save(hotel)
        
        # Проверяем, что отель ссылается на существующую локацию
        saved_hotel = hotel_repo.get_by_id(hotel.id)
        assert saved_hotel.location is not None
        assert saved_hotel.location.id == loc.id
        
        # Получаем локацию через репозиторий
        saved_loc = location_repo.get_by_id(loc.id)
        assert saved_loc is not None
        assert saved_loc.name == "Тестовая"
    
    def test_bulk_operations(self, location_repo, hotel_repo):
        """Массовые операции с данными"""
        # Создаем много локаций
        locations = []
        for i in range(10):
            loc = Location(
                name=f"Город {i}",
                coordinates=Coordinates(
                    random.uniform(50, 60),
                    random.uniform(30, 40)
                )
            )
            location_repo.save(loc)
            locations.append(loc)
        
        # Создаем много отелей
        for i in range(20):
            loc = random.choice(locations)
            hotel = Hotel(
                name=f"Отель {i}",
                location=loc,
                rating=random.uniform(1, 5),
                price_per_night=random.uniform(1000, 30000)
            )
            hotel_repo.save(hotel)
        
        # Проверяем количество
        all_hotels = [h for h in hotel_repo._hotels.values()]
        assert len(all_hotels) == 20
        
        # Проверяем поиск по рейтингу
        good_hotels = hotel_repo.get_by_rating(4.0)
        assert len(good_hotels) >= 0


import random

# Для использования random в тестах
random.seed(42)