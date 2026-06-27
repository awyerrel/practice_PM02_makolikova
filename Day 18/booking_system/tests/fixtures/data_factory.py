# tests/fixtures/data_factory.py
"""
Фабрика тестовых данных для системы логистики и бронирования

Использует factory-boy и faker для генерации реалистичных тестовых данных.
Поддерживает создание сущностей доменной модели, DTO и тестовых сценариев.
"""
import random
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from decimal import Decimal

import factory
from factory import Faker, SubFactory, LazyAttribute, Sequence
from faker import Faker as RealFaker

from src.core.domain import (
    Coordinates, Location, Hotel, Route, RouteSegment,
    TransportType, Route as RouteAggregate
)
from src.application.dto import (
    CoordinatesDTO, LocationDTO, HotelDTO, RouteDTO,
    RouteSegmentDTO, RouteOptimizationRequest
)
from src.core.exceptions import ValidationError

# Инициализация Faker для русского языка
fake = RealFaker('ru_RU')

# --- Базовые фабрики ---

class CoordinatesFactory(factory.Factory):
    """Фабрика для создания Coordinates"""
    class Meta:
        model = Coordinates
    
    lat = factory.LazyAttribute(
        lambda _: round(random.uniform(-90, 90), 6)
    )
    lon = factory.LazyAttribute(
        lambda _: round(random.uniform(-180, 180), 6)
    )
    
    @classmethod
    def moscow(cls) -> Coordinates:
        """Координаты Москвы"""
        return Coordinates(55.7558, 37.6173)
    
    @classmethod
    def spb(cls) -> Coordinates:
        """Координаты Санкт-Петербурга"""
        return Coordinates(59.9343, 30.3351)
    
    @classmethod
    def ekaterinburg(cls) -> Coordinates:
        """Координаты Екатеринбурга"""
        return Coordinates(56.8389, 60.6057)
    
    @classmethod
    def kazan(cls) -> Coordinates:
        """Координаты Казани"""
        return Coordinates(55.7887, 49.1221)
    
    @classmethod
    def novosibirsk(cls) -> Coordinates:
        """Координаты Новосибирска"""
        return Coordinates(55.0084, 82.9357)
    
    @classmethod
    def vladivostok(cls) -> Coordinates:
        """Координаты Владивостока"""
        return Coordinates(43.1155, 131.8855)
    
    @classmethod
    def sochi(cls) -> Coordinates:
        """Координаты Сочи"""
        return Coordinates(43.6028, 39.7342)


class LocationFactory(factory.Factory):
    """Фабрика для создания Location"""
    class Meta:
        model = Location
    
    id = Sequence(lambda n: n + 1)
    name = Faker('city', locale='ru_RU')
    coordinates = SubFactory(CoordinatesFactory)
    address = Faker('address', locale='ru_RU')
    city = Faker('city', locale='ru_RU')
    country = factory.LazyAttribute(lambda _: random.choice(['Россия', 'Беларусь', 'Казахстан']))
    
    @classmethod
    def moscow(cls) -> Location:
        """Локация Москва"""
        return Location(
            id=1,
            name="Москва",
            coordinates=CoordinatesFactory.moscow(),
            address="г. Москва, Красная площадь, 1",
            city="Москва",
            country="Россия"
        )
    
    @classmethod
    def spb(cls) -> Location:
        """Локация Санкт-Петербург"""
        return Location(
            id=2,
            name="Санкт-Петербург",
            coordinates=CoordinatesFactory.spb(),
            address="г. Санкт-Петербург, Невский пр., 1",
            city="Санкт-Петербург",
            country="Россия"
        )
    
    @classmethod
    def ekaterinburg(cls) -> Location:
        """Локация Екатеринбург"""
        return Location(
            id=3,
            name="Екатеринбург",
            coordinates=CoordinatesFactory.ekaterinburg(),
            address="г. Екатеринбург, ул. Ленина, 1",
            city="Екатеринбург",
            country="Россия"
        )
    
    @classmethod
    def create_with_coordinates(cls, lat: float, lon: float, **kwargs) -> Location:
        """Создать локацию с конкретными координатами"""
        return Location(
            coordinates=Coordinates(lat, lon),
            **kwargs
        )


class HotelFactory(factory.Factory):
    """Фабрика для создания Hotel"""
    class Meta:
        model = Hotel
    
    id = Sequence(lambda n: n + 1)
    name = Faker('company', locale='ru_RU')
    location = SubFactory(LocationFactory)
    rating = factory.LazyAttribute(
        lambda _: round(random.uniform(1.0, 5.0), 1)
    )
    price_per_night = factory.LazyAttribute(
        lambda _: round(random.uniform(2000, 50000), 2)
    )
    available_rooms = factory.LazyAttribute(
        lambda _: random.randint(0, 50)
    )
    amenities = factory.LazyAttribute(
        lambda _: random.sample([
            'WiFi', 'Парковка', 'Ресторан', 'Бассейн',
            'Спортзал', 'СПА', 'Кондиционер', 'ТВ',
            'Мини-бар', 'Сейф', 'Вид на море', 'Терраса'
        ], k=random.randint(3, 7))
    )
    
    @classmethod
    def luxury_hotel(cls) -> Hotel:
        """Роскошный отель"""
        return Hotel(
            name="Grand Hotel",
            location=LocationFactory.moscow(),
            rating=4.9,
            price_per_night=35000.0,
            available_rooms=20,
            amenities=['WiFi', 'СПА', 'Ресторан', 'Бассейн', 'Консьерж']
        )
    
    @classmethod
    def budget_hotel(cls) -> Hotel:
        """Бюджетный отель"""
        return Hotel(
            name="Budget Inn",
            location=LocationFactory.moscow(),
            rating=3.2,
            price_per_night=2500.0,
            available_rooms=30,
            amenities=['WiFi', 'Парковка']
        )
    
    @classmethod
    def create_near_location(cls, location: Location, count: int = 5) -> List[Hotel]:
        """Создать отели рядом с локацией"""
        hotels = []
        for i in range(count):
            # Создаем координаты с небольшим смещением
            offset_lat = (random.random() - 0.5) * 0.01
            offset_lon = (random.random() - 0.5) * 0.01
            
            hotel_location = Location(
                id=i + 100,
                name=f"Отель {i+1}",
                coordinates=Coordinates(
                    location.coordinates.lat + offset_lat,
                    location.coordinates.lon + offset_lon
                ),
                address=f"{location.address}, стр. {i+1}",
                city=location.city,
                country=location.country
            )
            
            hotel = Hotel(
                id=i + 1000,
                name=f"Отель '{fake.company()}'",
                location=hotel_location,
                rating=round(random.uniform(3.0, 4.8), 1),
                price_per_night=round(random.uniform(3000, 30000), 2),
                available_rooms=random.randint(5, 40),
                amenities=random.sample([
                    'WiFi', 'Парковка', 'Ресторан', 'Бассейн'
                ], k=random.randint(2, 4))
            )
            hotels.append(hotel)
        
        return hotels


class RouteSegmentFactory(factory.Factory):
    """Фабрика для создания RouteSegment"""
    class Meta:
        model = RouteSegment
    
    start = SubFactory(LocationFactory)
    end = SubFactory(LocationFactory)
    transport_type = factory.LazyAttribute(
        lambda _: random.choice(list(TransportType))
    )
    distance_km = factory.LazyAttribute(
        lambda obj: obj.start.coordinates.distance_to(obj.end.coordinates)
        if obj.start.coordinates and obj.end.coordinates
        else random.uniform(10, 1000)
    )
    duration_min = factory.LazyAttribute(
        lambda obj: int(obj.distance_km / 60 * 60)
        if obj.distance_km > 0
        else random.randint(10, 600)
    )
    
    @classmethod
    def moscow_to_spb(cls) -> RouteSegment:
        """Сегмент Москва - Санкт-Петербург"""
        return RouteSegment(
            start=LocationFactory.moscow(),
            end=LocationFactory.spb(),
            transport_type=TransportType.CAR,
            distance_km=634,
            duration_min=480  # 8 часов
        )
    
    @classmethod
    def spb_to_ekaterinburg(cls) -> RouteSegment:
        """Сегмент Санкт-Петербург - Екатеринбург"""
        return RouteSegment(
            start=LocationFactory.spb(),
            end=LocationFactory.ekaterinburg(),
            transport_type=TransportType.TRAIN,
            distance_km=1800,
            duration_min=1140  # 19 часов
        )


class RouteFactory(factory.Factory):
    """Фабрика для создания Route"""
    class Meta:
        model = RouteAggregate
    
    id = Sequence(lambda n: n + 1)
    segments = factory.LazyAttribute(
        lambda _: [RouteSegmentFactory() for _ in range(random.randint(1, 5))]
    )
    total_distance = factory.LazyAttribute(
        lambda obj: sum(seg.distance_km for seg in obj.segments)
    )
    total_duration = factory.LazyAttribute(
        lambda obj: sum(seg.duration_min for seg in obj.segments)
    )
    created_at = factory.LazyAttribute(
        lambda _: datetime.now() - timedelta(days=random.randint(0, 30))
    )
    updated_at = factory.LazyAttribute(
        lambda _: datetime.now() - timedelta(days=random.randint(0, 7))
    )
    
    @classmethod
    def long_distance_route(cls) -> RouteAggregate:
        """Маршрут на дальнее расстояние"""
        start = LocationFactory.moscow()
        mid = LocationFactory.ekaterinburg()
        end = LocationFactory.vladivostok()
        
        segments = [
            RouteSegment(start, mid, TransportType.TRAIN),
            RouteSegment(mid, end, TransportType.PLANE)
        ]
        
        route = RouteAggregate(segments=segments)
        route.calculate_totals()
        return route
    
    @classmethod
    def city_route(cls) -> RouteAggregate:
        """Городской маршрут"""
        start = LocationFactory.moscow()
        
        # Создаем промежуточные точки в Москве
        points = [
            LocationFactory.create_with_coordinates(
                55.7558 + (random.random() - 0.5) * 0.02,
                37.6173 + (random.random() - 0.5) * 0.02,
                name=f"Точка {i+1}"
            )
            for i in range(3)
        ]
        
        end = LocationFactory.create_with_coordinates(
            55.7558 + (random.random() - 0.5) * 0.01,
            37.6173 + (random.random() - 0.5) * 0.01,
            name="Конец маршрута"
        )
        
        segments = []
        current = start
        for point in points:
            segments.append(RouteSegment(current, point, TransportType.CAR))
            current = point
        segments.append(RouteSegment(current, end, TransportType.WALK))
        
        route = RouteAggregate(segments=segments)
        route.calculate_totals()
        return route
    
    @classmethod
    def with_hotels(cls, hotel_count: int = 3) -> Tuple[RouteAggregate, List[Hotel]]:
        """Создать маршрут с отелями"""
        start = LocationFactory.moscow()
        end = LocationFactory.spb()
        
        # Создаем отели вдоль маршрута
        hotels = []
        for i in range(hotel_count):
            # Промежуточная локация
            lat = 55.7558 + (i + 1) * 0.4
            lon = 37.6173 + (i + 1) * 0.3
            
            hotel_location = Location(
                id=i + 200,
                name=f"Город {i+1}",
                coordinates=Coordinates(lat, lon),
                address=f"ул. Центральная, {i+1}",
                city=f"Город {i+1}",
                country="Россия"
            )
            
            hotel = Hotel(
                id=i + 1000,
                name=f"Отель {i+1}",
                location=hotel_location,
                rating=round(random.uniform(3.5, 4.8), 1),
                price_per_night=round(random.uniform(5000, 25000), 2),
                available_rooms=random.randint(10, 30),
                amenities=['WiFi', 'Ресторан', 'Парковка']
            )
            hotels.append(hotel)
        
        # Создаем сегменты маршрута через отели
        segments = []
        current = start
        for hotel in hotels:
            if hotel.location:
                segments.append(RouteSegment(
                    current,
                    hotel.location,
                    TransportType.CAR
                ))
                current = hotel.location
        
        segments.append(RouteSegment(current, end, TransportType.CAR))
        
        route = RouteAggregate(segments=segments)
        route.calculate_totals()
        
        return route, hotels


# --- DTO Фабрики ---

class CoordinatesDTOFactory(factory.Factory):
    """Фабрика для создания CoordinatesDTO"""
    class Meta:
        model = CoordinatesDTO
    
    lat = factory.LazyAttribute(
        lambda _: round(random.uniform(-90, 90), 6)
    )
    lon = factory.LazyAttribute(
        lambda _: round(random.uniform(-180, 180), 6)
    )
    
    @classmethod
    def from_coordinates(cls, coords: Coordinates) -> CoordinatesDTO:
        """Создать DTO из Coordinates"""
        return CoordinatesDTO(lat=coords.lat, lon=coords.lon)


class LocationDTOFactory(factory.Factory):
    """Фабрика для создания LocationDTO"""
    class Meta:
        model = LocationDTO
    
    id = Sequence(lambda n: n + 1)
    name = Faker('city', locale='ru_RU')
    coordinates = SubFactory(CoordinatesDTOFactory)
    address = Faker('address', locale='ru_RU')
    city = Faker('city', locale='ru_RU')
    country = factory.LazyAttribute(lambda _: random.choice(['Россия', 'Беларусь', 'Казахстан']))


class RouteSegmentDTOFactory(factory.Factory):
    """Фабрика для создания RouteSegmentDTO"""
    class Meta:
        model = RouteSegmentDTO
    
    start_location_id = factory.LazyAttribute(lambda _: random.randint(1, 100))
    end_location_id = factory.LazyAttribute(lambda _: random.randint(1, 100))
    transport_type = factory.LazyAttribute(
        lambda _: random.choice([t.value for t in TransportType])
    )
    distance_km = factory.LazyAttribute(
        lambda _: round(random.uniform(5, 1000), 2)
    )
    duration_min = factory.LazyAttribute(
        lambda _: random.randint(10, 600)
    )


class RouteDTOFactory(factory.Factory):
    """Фабрика для создания RouteDTO"""
    class Meta:
        model = RouteDTO
    
    id = Sequence(lambda n: n + 1)
    segments = factory.LazyAttribute(
        lambda _: [RouteSegmentDTOFactory() for _ in range(random.randint(1, 5))]
    )
    total_distance = factory.LazyAttribute(
        lambda obj: round(sum(seg.distance_km for seg in obj.segments), 2)
        if obj.segments else 0.0
    )
    total_duration = factory.LazyAttribute(
        lambda obj: sum(seg.duration_min for seg in obj.segments)
        if obj.segments else 0
    )
    departure_time = factory.LazyAttribute(
        lambda _: datetime.now() + timedelta(days=random.randint(1, 30))
    )


class HotelDTOFactory(factory.Factory):
    """Фабрика для создания HotelDTO"""
    class Meta:
        model = HotelDTO
    
    id = Sequence(lambda n: n + 1)
    name = Faker('company', locale='ru_RU')
    location = SubFactory(LocationDTOFactory)
    rating = factory.LazyAttribute(
        lambda _: round(random.uniform(1.0, 5.0), 1)
    )
    price_per_night = factory.LazyAttribute(
        lambda _: round(random.uniform(2000, 50000), 2)
    )
    available_rooms = factory.LazyAttribute(
        lambda _: random.randint(0, 50)
    )
    amenities = factory.LazyAttribute(
        lambda _: random.sample([
            'WiFi', 'Парковка', 'Ресторан', 'Бассейн',
            'Спортзал', 'СПА', 'Кондиционер'
        ], k=random.randint(3, 5))
    )


# --- Сценарии для тестов ---

class TestScenarioFactory:
    """Фабрика для создания тестовых сценариев"""
    
    @staticmethod
    def simple_booking_scenario() -> Dict[str, Any]:
        """Простой сценарий бронирования"""
        return {
            'hotel': HotelFactory.luxury_hotel(),
            'check_in': datetime.now() + timedelta(days=10),
            'check_out': datetime.now() + timedelta(days=15),
            'guests': 2,
            'room_type': 'suite'
        }
    
    @staticmethod
    def multi_city_route_scenario() -> Dict[str, Any]:
        """Сценарий маршрута по нескольким городам"""
        cities = [
            LocationFactory.moscow(),
            LocationFactory.spb(),
            LocationFactory.ekaterinburg(),
            LocationFactory.kazan()
        ]
        
        hotels_by_city = {
            city.name: HotelFactory.create_near_location(city, count=3)
            for city in cities
        }
        
        return {
            'cities': cities,
            'hotels': hotels_by_city,
            'transport': random.choice(['car', 'train', 'plane']),
            'days_per_city': random.randint(1, 5)
        }
    
    @staticmethod
    def complex_route_with_hotels() -> Dict[str, Any]:
        """Сложный маршрут с отелями"""
        start = LocationFactory.moscow()
        end = LocationFactory.vladivostok()
        
        # Промежуточные города
        waypoints = [
            LocationFactory.ekaterinburg(),
            LocationFactory.novosibirsk(),
            LocationFactory.kazan()
        ]
        
        # Отели в каждом городе
        hotel_groups = []
        for city in [start] + waypoints + [end]:
            hotels = HotelFactory.create_near_location(city, count=2)
            hotel_groups.append({
                'city': city,
                'hotels': hotels,
                'recommended': hotels[0] if hotels else None
            })
        
        return {
            'start': start,
            'end': end,
            'waypoints': waypoints,
            'hotel_groups': hotel_groups,
            'total_distance': sum(
                start.coordinates.distance_to(waypoint.coordinates)
                for waypoint in waypoints
            ) + waypoints[-1].coordinates.distance_to(end.coordinates) if waypoints else 0
        }
    
    @staticmethod
    def edge_case_scenario() -> Dict[str, Any]:
        """Сценарий с граничными случаями"""
        return {
            'zero_distance_route': RouteSegment(
                start=LocationFactory.moscow(),
                end=LocationFactory.moscow(),
                transport_type=TransportType.WALK,
                distance_km=0
            ),
            'empty_hotels': [],
            'single_hotel': HotelFactory.budget_hotel(),
            'invalid_coordinates': Coordinates(100, 200),  # Невалидные координаты
            'negative_price': -1000.0,
            'zero_rooms': Hotel(
                name="No Rooms Hotel",
                available_rooms=0,
                rating=4.0
            )
        }
    
    @staticmethod
    def performance_test_scenario(count: int = 100) -> Dict[str, Any]:
        """Сценарий для тестирования производительности"""
        locations = [LocationFactory() for _ in range(count)]
        hotels = [HotelFactory() for _ in range(count // 2)]
        
        # Создаем много маршрутов
        routes = []
        for i in range(count // 10):
            start = random.choice(locations)
            end = random.choice(locations)
            if start != end:
                route = RouteAggregate(segments=[
                    RouteSegment(start, end, TransportType.CAR)
                ])
                routes.append(route)
        
        return {
            'locations': locations,
            'hotels': hotels,
            'routes': routes,
            'total_objects': len(locations) + len(hotels) + len(routes)
        }


# --- Утилиты для тестов ---

class TestDataHelper:
    """Вспомогательные методы для работы с тестовыми данными"""
    
    @staticmethod
    def create_test_hotel_chain(count: int = 5) -> List[Hotel]:
        """Создать цепочку отелей"""
        hotels = []
        base_lat = 55.7558
        base_lon = 37.6173
        
        for i in range(count):
            lat = base_lat + i * 0.1
            lon = base_lon + i * 0.1
            
            location = Location(
                id=i + 100,
                name=f"Location {i+1}",
                coordinates=Coordinates(lat, lon),
                address=f"ул. Тестовая, {i+1}",
                city=f"Город {i+1}",
                country="Россия"
            )
            
            hotel = Hotel(
                id=i + 1000,
                name=f"Hotel {i+1}",
                location=location,
                rating=round(3.0 + i * 0.3, 1),
                price_per_night=round(3000 + i * 1000, 2),
                available_rooms=random.randint(5, 30),
                amenities=['WiFi', 'Парковка', 'Ресторан'] if i % 2 == 0 else ['WiFi']
            )
            hotels.append(hotel)
        
        return hotels
    
    @staticmethod
    def generate_route_with_optimal_path(
        start: Location,
        end: Location,
        hotels: List[Hotel]
    ) -> List[Location]:
        """Сгенерировать оптимальный путь через отели"""
        if not hotels:
            return [start, end]
        
        # Сортировка отелей по расстоянию до старта
        sorted_hotels = sorted(
            hotels,
            key=lambda h: h.location.coordinates.distance_to(start.coordinates)
            if h.location and h.location.coordinates
            else float('inf')
        )
        
        # Выбираем ближайшие отели
        selected = sorted_hotels[:min(3, len(sorted_hotels))]
        
        path = [start]
        current = start
        
        for hotel in selected:
            if hotel.location and hotel.location.coordinates:
                # Проверяем, что отель не слишком далеко
                dist = current.coordinates.distance_to(hotel.location.coordinates)
                if dist < 200:  # Не дальше 200 км
                    path.append(hotel.location)
                    current = hotel.location
        
        path.append(end)
        return path
    
    @staticmethod
    def create_route_with_waypoints(
        locations: List[Location],
        transport_type: TransportType = TransportType.CAR
    ) -> RouteAggregate:
        """Создать маршрут с указанными точками"""
        if len(locations) < 2:
            raise ValueError("Need at least 2 locations")
        
        segments = []
        for i in range(len(locations) - 1):
            segment = RouteSegment(
                start=locations[i],
                end=locations[i + 1],
                transport_type=transport_type
            )
            segments.append(segment)
        
        route = RouteAggregate(segments=segments)
        route.calculate_totals()
        return route


# --- Pytest Fixtures ---

import pytest

@pytest.fixture
def moscow_location():
    """Фикстура: Москва"""
    return LocationFactory.moscow()

@pytest.fixture
def spb_location():
    """Фикстура: Санкт-Петербург"""
    return LocationFactory.spb()

@pytest.fixture
def ekaterinburg_location():
    """Фикстура: Екатеринбург"""
    return LocationFactory.ekaterinburg()

@pytest.fixture
def test_hotels():
    """Фикстура: список тестовых отелей"""
    return HotelFactory.create_near_location(
        LocationFactory.moscow(),
        count=5
    )

@pytest.fixture
def sample_route():
    """Фикстура: тестовый маршрут"""
    start = LocationFactory.moscow()
    end = LocationFactory.spb()
    
    segments = [
        RouteSegment(start, end, TransportType.CAR)
    ]
    
    route = RouteAggregate(segments=segments)
    route.calculate_totals()
    return route

@pytest.fixture
def complex_route():
    """Фикстура: сложный маршрут"""
    route, hotels = RouteFactory.with_hotels(hotel_count=3)
    return route

@pytest.fixture
def optimization_request():
    """Фикстура: запрос на оптимизацию маршрута"""
    start = LocationFactory.moscow()
    end = LocationFactory.spb()
    hotels = HotelFactory.create_near_location(
        LocationFactory.moscow(),
        count=3
    )
    
    return RouteOptimizationRequest(
        start_location_id=start.id or 1,
        end_location_id=end.id or 2,
        hotel_ids=[h.id or i + 100 for i, h in enumerate(hotels)],
        transport_type="car"
    )


# --- Примеры использования ---

if __name__ == "__main__":
    # Примеры создания тестовых данных
    
    # 1. Создание одного отеля
    hotel = HotelFactory.luxury_hotel()
    print(f"Luxury Hotel: {hotel.name}, Rating: {hotel.rating}")
    
    # 2. Создание списка отелей
    hotels = HotelFactory.create_near_location(
        LocationFactory.moscow(),
        count=3
    )
    print(f"Created {len(hotels)} hotels near Moscow")
    
    # 3. Создание маршрута
    route = RouteFactory.long_distance_route()
    print(f"Route: {len(route.segments)} segments, {route.total_distance:.0f} km")
    
    # 4. Создание сложного сценария
    scenario = TestScenarioFactory.complex_route_with_hotels()
    print(f"Complex scenario: {len(scenario['hotel_groups'])} hotel groups")
    
    # 5. Создание DTO
    route_dto = RouteDTOFactory()
    print(f"Route DTO: {len(route_dto.segments)} segments")
    
    # 6. Тестовый набор данных
    helper = TestDataHelper()
    hotels_chain = helper.create_test_hotel_chain(5)
    print(f"Hotel chain: {len(hotels_chain)} hotels")
    
    # 7. Оптимизация маршрута
    path = helper.generate_route_with_optimal_path(
        LocationFactory.moscow(),
        LocationFactory.spb(),
        hotels_chain
    )
    print(f"Optimized path: {len(path)} points")