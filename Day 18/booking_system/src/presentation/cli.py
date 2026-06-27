# src/presentation/cli.py
"""
CLI интерфейс для системы логистики и бронирования

Предоставляет команды для:
- Управления локациями
- Управления отелями
- Создания и оптимизации маршрутов
- Просмотра статистики
- Импорта/экспорта данных

Использует библиотеку click для удобного создания CLI команд
"""
import click
import json
import sys
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from tabulate import tabulate
import os
from pathlib import Path

from src.core.domain import (
    Location, Coordinates, Hotel, Route, RouteSegment,
    TransportType
)
from src.core.exceptions import ValidationError, NotFoundError
from src.application.services import (
    RouteService, HotelLocationService, RouteOptimizationService
)
from src.application.dto import (
    RouteDTO, RouteSegmentDTO, HotelDTO, 
    RouteOptimizationRequest, CoordinatesDTO
)
from src.infrastructure.repositories import (
    InMemoryLocationRepository,
    InMemoryHotelRepository,
    InMemoryRouteRepository
)
from src.infrastructure.external_api import MockMappingService
from src.infrastructure.uow import UnitOfWorkManager, InMemoryUnitOfWork


# --- Инициализация зависимостей ---
location_repo = InMemoryLocationRepository()
hotel_repo = InMemoryHotelRepository()
route_repo = InMemoryRouteRepository()
mapping_service = MockMappingService()

route_service = RouteService(route_repo, location_repo, hotel_repo)
hotel_service = HotelLocationService(hotel_repo, location_repo)
optimization_service = RouteOptimizationService(
    location_repo, hotel_repo, mapping_service
)

uow_manager = UnitOfWorkManager()


# --- Утилиты для CLI ---

def print_table(data: List[Dict], headers: List[str]) -> None:
    """Вывести таблицу в консоль"""
    if not data:
        click.echo("Нет данных")
        return
    
    table_data = []
    for item in data:
        row = []
        for header in headers:
            value = item.get(header, '')
            if isinstance(value, float):
                value = f"{value:.2f}"
            row.append(value)
        table_data.append(row)
    
    click.echo(tabulate(table_data, headers=headers, tablefmt="grid"))


def print_success(message: str) -> None:
    """Вывести сообщение об успехе"""
    click.echo(click.style(f"✅ {message}", fg="green"))


def print_error(message: str) -> None:
    """Вывести сообщение об ошибке"""
    click.echo(click.style(f"❌ {message}", fg="red"))


def print_info(message: str) -> None:
    """Вывести информационное сообщение"""
    click.echo(click.style(f"ℹ️ {message}", fg="blue"))


def print_warning(message: str) -> None:
    """Вывести предупреждение"""
    click.echo(click.style(f"⚠️ {message}", fg="yellow"))


def parse_coordinates(lat_str: str, lon_str: str) -> Coordinates:
    """Разобрать координаты из строк"""
    try:
        lat = float(lat_str)
        lon = float(lon_str)
        return Coordinates(lat, lon)
    except ValueError:
        raise click.BadParameter("Неверный формат координат")


def parse_date(date_str: str) -> datetime:
    """Разобрать дату из строки"""
    try:
        return datetime.fromisoformat(date_str)
    except ValueError:
        raise click.BadParameter("Неверный формат даты. Используйте YYYY-MM-DD")


# --- Группы команд ---

@click.group()
def cli():
    """
    Система управления логистикой и бронированием
    
    Команды для работы с локациями, отелями и маршрутами.
    """
    pass


# --- Команды для управления локациями ---

@cli.group()
def location():
    """Управление локациями"""
    pass


@location.command('create')
@click.option('--name', '-n', required=True, help="Название локации")
@click.option('--lat', '-l', required=True, help="Широта")
@click.option('--lon', '-L', required=True, help="Долгота")
@click.option('--address', '-a', help="Адрес")
@click.option('--city', '-c', help="Город")
@click.option('--country', '-C', help="Страна")
def location_create(name: str, lat: str, lon: str, address: str, city: str, country: str):
    """Создать новую локацию"""
    try:
        coords = parse_coordinates(lat, lon)
        
        location = Location(
            name=name,
            coordinates=coords,
            address=address or "",
            city=city or "",
            country=country or ""
        )
        
        with InMemoryUnitOfWork() as uow:
            repo = uow.get_repository('location')
            saved = repo.save(location)
        
        print_success(f"Локация создана: ID={saved.id}, Название={saved.name}")
        print_info(f"Координаты: {saved.coordinates.lat}, {saved.coordinates.lon}")
        
    except ValidationError as e:
        print_error(f"Ошибка валидации: {e}")
    except Exception as e:
        print_error(f"Ошибка: {e}")


@location.command('list')
@click.option('--city', '-c', help="Фильтр по городу")
@click.option('--country', '-C', help="Фильтр по стране")
def location_list(city: str, country: str):
    """Показать список локаций"""
    locations = list(location_repo._locations.values())
    
    if city:
        locations = [l for l in locations if l.city == city]
    if country:
        locations = [l for l in locations if l.country == country]
    
    if not locations:
        print_info("Локации не найдены")
        return
    
    data = []
    for loc in locations:
        data.append({
            'ID': loc.id,
            'Название': loc.name,
            'Город': loc.city,
            'Страна': loc.country,
            'Координаты': f"{loc.coordinates.lat:.4f}, {loc.coordinates.lon:.4f}" if loc.coordinates else "Нет"
        })
    
    print_table(data, ['ID', 'Название', 'Город', 'Страна', 'Координаты'])


@location.command('get')
@click.argument('location_id', type=int)
def location_get(location_id: int):
    """Показать информацию о локации"""
    location = location_repo.get_by_id(location_id)
    
    if not location:
        print_error(f"Локация с ID {location_id} не найдена")
        return
    
    click.echo("\n" + "="*50)
    click.echo(f"ЛОКАЦИЯ #{location.id}")
    click.echo("="*50)
    click.echo(f"Название: {location.name}")
    click.echo(f"Адрес: {location.address}")
    click.echo(f"Город: {location.city}")
    click.echo(f"Страна: {location.country}")
    if location.coordinates:
        click.echo(f"Широта: {location.coordinates.lat:.6f}")
        click.echo(f"Долгота: {location.coordinates.lon:.6f}")
    click.echo("="*50)


@location.command('delete')
@click.argument('location_id', type=int)
@click.confirmation_option(prompt="Вы уверены, что хотите удалить локацию?")
def location_delete(location_id: int):
    """Удалить локацию"""
    location = location_repo.get_by_id(location_id)
    
    if not location:
        print_error(f"Локация с ID {location_id} не найдена")
        return
    
    try:
        with InMemoryUnitOfWork() as uow:
            repo = uow.get_repository('location')
            # Удаляем из репозитория
            del repo._locations[location_id]
        
        print_success(f"Локация #{location_id} удалена")
    except Exception as e:
        print_error(f"Ошибка при удалении: {e}")


# --- Команды для управления отелями ---

@cli.group()
def hotel():
    """Управление отелями"""
    pass


@hotel.command('create')
@click.option('--name', '-n', required=True, help="Название отеля")
@click.option('--location-id', '-l', type=int, required=True, help="ID локации")
@click.option('--rating', '-r', type=float, default=3.0, help="Рейтинг (1.0-5.0)")
@click.option('--price', '-p', type=float, default=5000.0, help="Цена за ночь")
@click.option('--rooms', '-R', type=int, default=10, help="Количество доступных комнат")
@click.option('--amenities', '-a', multiple=True, help="Удобства (можно указать несколько)")
def hotel_create(name: str, location_id: int, rating: float, price: float, rooms: int, amenities: tuple):
    """Создать новый отель"""
    try:
        location = location_repo.get_by_id(location_id)
        if not location:
            print_error(f"Локация с ID {location_id} не найдена")
            return
        
        if not (1.0 <= rating <= 5.0):
            print_error("Рейтинг должен быть от 1.0 до 5.0")
            return
        
        hotel = Hotel(
            name=name,
            location=location,
            rating=rating,
            price_per_night=price,
            available_rooms=rooms,
            amenities=list(amenities) if amenities else []
        )
        
        with InMemoryUnitOfWork() as uow:
            repo = uow.get_repository('hotel')
            saved = repo.save(hotel)
        
        print_success(f"Отель создан: ID={saved.id}, Название={saved.name}")
        print_info(f"Локация: {location.name}, Рейтинг: {saved.rating}")
        
    except ValidationError as e:
        print_error(f"Ошибка валидации: {e}")
    except Exception as e:
        print_error(f"Ошибка: {e}")


@hotel.command('list')
@click.option('--min-rating', '-r', type=float, help="Минимальный рейтинг")
@click.option('--location-id', '-l', type=int, help="ID локации")
@click.option('--max-price', '-p', type=float, help="Максимальная цена")
def hotel_list(min_rating: float, location_id: int, max_price: float):
    """Показать список отелей"""
    hotels = list(hotel_repo._hotels.values())
    
    if min_rating:
        hotels = [h for h in hotels if h.rating >= min_rating]
    if location_id:
        hotels = [h for h in hotels if h.location and h.location.id == location_id]
    if max_price:
        hotels = [h for h in hotels if h.price_per_night <= max_price]
    
    if not hotels:
        print_info("Отели не найдены")
        return
    
    data = []
    for h in hotels:
        data.append({
            'ID': h.id,
            'Название': h.name,
            'Рейтинг': f"{h.rating:.1f}",
            'Цена/ночь': f"{h.price_per_night:.0f}₽",
            'Комнаты': h.available_rooms,
            'Локация': h.location.name if h.location else "Нет",
            'Удобства': ', '.join(h.amenities[:3]) + ('...' if len(h.amenities) > 3 else '')
        })
    
    print_table(data, ['ID', 'Название', 'Рейтинг', 'Цена/ночь', 'Комнаты', 'Локация', 'Удобства'])


@hotel.command('get')
@click.argument('hotel_id', type=int)
def hotel_get(hotel_id: int):
    """Показать информацию об отеле"""
    hotel = hotel_repo.get_by_id(hotel_id)
    
    if not hotel:
        print_error(f"Отель с ID {hotel_id} не найден")
        return
    
    click.echo("\n" + "="*50)
    click.echo(f"ОТЕЛЬ #{hotel.id}")
    click.echo("="*50)
    click.echo(f"Название: {hotel.name}")
    click.echo(f"Рейтинг: {hotel.rating:.1f}")
    click.echo(f"Цена за ночь: {hotel.price_per_night:.2f}₽")
    click.echo(f"Доступные комнаты: {hotel.available_rooms}")
    click.echo(f"Локация: {hotel.location.name if hotel.location else 'Нет'}")
    click.echo(f"Удобства: {', '.join(hotel.amenities) if hotel.amenities else 'Нет'}")
    click.echo("="*50)


@hotel.command('search')
@click.option('--location-id', '-l', type=int, required=True, help="ID локации")
@click.option('--radius', '-r', type=float, default=10.0, help="Радиус поиска в км")
def hotel_search(location_id: int, radius: float):
    """Поиск отелей рядом с локацией"""
    try:
        hotels = hotel_service.get_nearby_hotels(location_id, radius)
        
        if not hotels:
            print_info(f"Отели не найдены в радиусе {radius} км")
            return
        
        location = location_repo.get_by_id(location_id)
        
        data = []
        for h in hotels:
            if h.location and h.location.coordinates and location and location.coordinates:
                dist = location.coordinates.distance_to(h.location.coordinates)
            else:
                dist = 0
            
            data.append({
                'ID': h.id,
                'Название': h.name,
                'Рейтинг': f"{h.rating:.1f}",
                'Цена': f"{h.price_per_night:.0f}₽",
                'Расстояние': f"{dist:.1f} км",
                'Комнаты': h.available_rooms
            })
        
        print_info(f"Найдено {len(hotels)} отелей в радиусе {radius} км")
        print_table(data, ['ID', 'Название', 'Рейтинг', 'Цена', 'Расстояние', 'Комнаты'])
        
    except Exception as e:
        print_error(f"Ошибка при поиске: {e}")


# --- Команды для управления маршрутами ---

@cli.group()
def route():
    """Управление маршрутами"""
    pass


@route.command('create')
@click.option('--segments', '-s', required=True, help="JSON с сегментами маршрута")
def route_create(segments: str):
    """
    Создать маршрут
    
    Пример JSON:
    '[{"start_id": 1, "end_id": 2, "transport": "car"}]'
    """
    try:
        segments_data = json.loads(segments)
        
        route_dto = RouteDTO(
            segments=[
                RouteSegmentDTO(
                    start_location_id=s['start_id'],
                    end_location_id=s['end_id'],
                    transport_type=s.get('transport', 'car')
                )
                for s in segments_data
            ]
        )
        
        with InMemoryUnitOfWork() as uow:
            route = route_service.create_route_from_dto(route_dto)
        
        print_success(f"Маршрут создан: ID={route.id}")
        print_info(f"Дистанция: {route.total_distance:.2f} км")
        print_info(f"Длительность: {route.total_duration} мин")
        print_info(f"Сегментов: {len(route.segments)}")
        
        # Показываем детали маршрута
        click.echo("\n" + "="*50)
        click.echo("ДЕТАЛИ МАРШРУТА")
        click.echo("="*50)
        for i, seg in enumerate(route.segments, 1):
            click.echo(f"{i}. {seg.start.name} → {seg.end.name}")
            click.echo(f"   Дистанция: {seg.distance_km:.2f} км")
            click.echo(f"   Время: {seg.duration_min} мин")
            click.echo(f"   Транспорт: {seg.transport_type.value}")
            click.echo("-" * 40)
        
    except json.JSONDecodeError:
        print_error("Неверный формат JSON")
    except ValidationError as e:
        print_error(f"Ошибка валидации: {e}")
    except Exception as e:
        print_error(f"Ошибка: {e}")


@route.command('list')
@click.option('--limit', '-l', type=int, default=10, help="Лимит записей")
def route_list(limit: int):
    """Показать список маршрутов"""
    routes = list(route_repo._routes.values())[-limit:]
    
    if not routes:
        print_info("Маршруты не найдены")
        return
    
    data = []
    for r in routes:
        first_seg = r.segments[0] if r.segments else None
        last_seg = r.segments[-1] if r.segments else None
        
        data.append({
            'ID': r.id,
            'Старт': first_seg.start.name if first_seg else "Нет",
            'Финиш': last_seg.end.name if last_seg else "Нет",
            'Дистанция': f"{r.total_distance:.1f} км",
            'Время': f"{r.total_duration} мин",
            'Сегментов': len(r.segments)
        })
    
    print_table(data, ['ID', 'Старт', 'Финиш', 'Дистанция', 'Время', 'Сегментов'])


@route.command('get')
@click.argument('route_id', type=int)
def route_get(route_id: int):
    """Показать информацию о маршруте"""
    try:
        route = route_service.get_route_by_id(route_id)
        
        click.echo("\n" + "="*50)
        click.echo(f"МАРШРУТ #{route.id}")
        click.echo("="*50)
        click.echo(f"Общая дистанция: {route.total_distance:.2f} км")
        click.echo(f"Общее время: {route.total_duration} мин")
        click.echo(f"Создан: {route.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        click.echo(f"Количество сегментов: {len(route.segments)}")
        click.echo("\nСЕГМЕНТЫ:")
        click.echo("-" * 50)
        
        for i, seg in enumerate(route.segments, 1):
            click.echo(f"{i}. {seg.start.name} → {seg.end.name}")
            click.echo(f"   Дистанция: {seg.distance_km:.2f} км")
            click.echo(f"   Время: {seg.duration_min} мин")
            click.echo(f"   Транспорт: {seg.transport_type.value}")
            click.echo("-" * 40)
        
    except NotFoundError:
        print_error(f"Маршрут с ID {route_id} не найден")
    except Exception as e:
        print_error(f"Ошибка: {e}")


@route.command('optimize')
@click.option('--start-id', '-s', type=int, required=True, help="ID начальной локации")
@click.option('--end-id', '-e', type=int, required=True, help="ID конечной локации")
@click.option('--hotel-ids', '-h', help="Список ID отелей через запятую")
@click.option('--transport', '-t', default='car', help="Тип транспорта")
def route_optimize(start_id: int, end_id: int, hotel_ids: str, transport: str):
    """Оптимизировать маршрут с посещением отелей"""
    try:
        # Разбираем список отелей
        hotel_id_list = []
        if hotel_ids:
            hotel_id_list = [int(x.strip()) for x in hotel_ids.split(',')]
        
        request = RouteOptimizationRequest(
            start_location_id=start_id,
            end_location_id=end_id,
            hotel_ids=hotel_id_list,
            transport_type=transport
        )
        
        with InMemoryUnitOfWork() as uow:
            route = optimization_service.optimize_route(request)
        
        print_success(f"Маршрут оптимизирован: ID={route.id}")
        print_info(f"Дистанция: {route.total_distance:.2f} км")
        print_info(f"Время: {route.total_duration} мин")
        print_info(f"Посещено отелей: {len(hotel_id_list)}")
        
        # Показываем детали
        click.echo("\n" + "="*50)
        click.echo("ОПТИМИЗИРОВАННЫЙ МАРШРУТ")
        click.echo("="*50)
        for i, seg in enumerate(route.segments, 1):
            start_name = seg.start.name if seg.start else f"Точка {i}"
            end_name = seg.end.name if seg.end else f"Точка {i+1}"
            click.echo(f"{i}. {start_name} → {end_name}")
            click.echo(f"   Дистанция: {seg.distance_km:.2f} км")
            click.echo(f"   Время: {seg.duration_min} мин")
            click.echo("-" * 40)
        
    except ValidationError as e:
        print_error(f"Ошибка валидации: {e}")
    except Exception as e:
        print_error(f"Ошибка: {e}")


# --- Команды для статистики ---

@cli.group()
def stats():
    """Статистика системы"""
    pass


@stats.command('locations')
def stats_locations():
    """Статистика по локациям"""
    locations = list(location_repo._locations.values())
    
    if not locations:
        print_info("Нет данных о локациях")
        return
    
    cities = {}
    countries = {}
    
    for loc in locations:
        city = loc.city or "Не указан"
        country = loc.country or "Не указана"
        
        cities[city] = cities.get(city, 0) + 1
        countries[country] = countries.get(country, 0) + 1
    
    click.echo("="*50)
    click.echo("СТАТИСТИКА ЛОКАЦИЙ")
    click.echo("="*50)
    click.echo(f"Всего локаций: {len(locations)}")
    
    click.echo("\nПо городам:")
    for city, count in sorted(cities.items(), key=lambda x: x[1], reverse=True):
        click.echo(f"  {city}: {count}")
    
    click.echo("\nПо странам:")
    for country, count in sorted(countries.items(), key=lambda x: x[1], reverse=True):
        click.echo(f"  {country}: {count}")


@stats.command('hotels')
def stats_hotels():
    """Статистика по отелям"""
    hotels = list(hotel_repo._hotels.values())
    
    if not hotels:
        print_info("Нет данных об отелях")
        return
    
    avg_rating = sum(h.rating for h in hotels) / len(hotels) if hotels else 0
    avg_price = sum(h.price_per_night for h in hotels) / len(hotels) if hotels else 0
    total_rooms = sum(h.available_rooms for h in hotels)
    
    rating_distribution = {}
    for h in hotels:
        rating_range = f"{int(h.rating)}-{int(h.rating)+1}"
        rating_distribution[rating_range] = rating_distribution.get(rating_range, 0) + 1
    
    click.echo("="*50)
    click.echo("СТАТИСТИКА ОТЕЛЕЙ")
    click.echo("="*50)
    click.echo(f"Всего отелей: {len(hotels)}")
    click.echo(f"Средний рейтинг: {avg_rating:.2f}")
    click.echo(f"Средняя цена: {avg_price:.2f}₽")
    click.echo(f"Всего комнат: {total_rooms}")
    
    click.echo("\nРаспределение по рейтингу:")
    for rating_range, count in sorted(rating_distribution.items()):
        click.echo(f"  {rating_range}: {count}")


@stats.command('routes')
def stats_routes():
    """Статистика по маршрутам"""
    routes = list(route_repo._routes.values())
    
    if not routes:
        print_info("Нет данных о маршрутах")
        return
    
    total_distance = sum(r.total_distance for r in routes)
    total_duration = sum(r.total_duration for r in routes)
    avg_distance = total_distance / len(routes) if routes else 0
    avg_duration = total_duration / len(routes) if routes else 0
    
    transport_types = {}
    for r in routes:
        for seg in r.segments:
            transport = seg.transport_type.value
            transport_types[transport] = transport_types.get(transport, 0) + 1
    
    click.echo("="*50)
    click.echo("СТАТИСТИКА МАРШРУТОВ")
    click.echo("="*50)
    click.echo(f"Всего маршрутов: {len(routes)}")
    click.echo(f"Общая дистанция: {total_distance:.2f} км")
    click.echo(f"Средняя дистанция: {avg_distance:.2f} км")
    click.echo(f"Общее время: {total_duration} мин")
    click.echo(f"Среднее время: {avg_duration:.0f} мин")
    
    click.echo("\nТипы транспорта:")
    for transport, count in sorted(transport_types.items(), key=lambda x: x[1], reverse=True):
        click.echo(f"  {transport}: {count}")


# --- Команды для импорта/экспорта данных ---

@cli.group()
def data():
    """Импорт и экспорт данных"""
    pass


@data.command('export')
@click.option('--file', '-f', default='export.json', help="Имя файла для экспорта")
@click.option('--include-locations', is_flag=True, default=True, help="Включить локации")
@click.option('--include-hotels', is_flag=True, default=True, help="Включить отели")
@click.option('--include-routes', is_flag=True, default=True, help="Включить маршруты")
def data_export(file: str, include_locations: bool, include_hotels: bool, include_routes: bool):
    """Экспортировать данные в JSON файл"""
    try:
        data = {}
        
        if include_locations:
            locations = []
            for loc in location_repo._locations.values():
                locations.append({
                    'id': loc.id,
                    'name': loc.name,
                    'lat': loc.coordinates.lat if loc.coordinates else None,
                    'lon': loc.coordinates.lon if loc.coordinates else None,
                    'address': loc.address,
                    'city': loc.city,
                    'country': loc.country
                })
            data['locations'] = locations
        
        if include_hotels:
            hotels = []
            for h in hotel_repo._hotels.values():
                hotels.append({
                    'id': h.id,
                    'name': h.name,
                    'location_id': h.location.id if h.location else None,
                    'rating': h.rating,
                    'price_per_night': h.price_per_night,
                    'available_rooms': h.available_rooms,
                    'amenities': h.amenities
                })
            data['hotels'] = hotels
        
        if include_routes:
            routes = []
            for r in route_repo._routes.values():
                routes.append({
                    'id': r.id,
                    'segments': [
                        {
                            'start_id': seg.start.id if seg.start else None,
                            'end_id': seg.end.id if seg.end else None,
                            'transport': seg.transport_type.value,
                            'distance': seg.distance_km,
                            'duration': seg.duration_min
                        }
                        for seg in r.segments
                    ]
                })
            data['routes'] = routes
        
        with open(file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        
        print_success(f"Данные экспортированы в {file}")
        print_info(f"Локаций: {len(data.get('locations', []))}")
        print_info(f"Отелей: {len(data.get('hotels', []))}")
        print_info(f"Маршрутов: {len(data.get('routes', []))}")
        
    except Exception as e:
        print_error(f"Ошибка при экспорте: {e}")


@data.command('import')
@click.argument('file', type=click.Path(exists=True))
def data_import(file: str):
    """Импортировать данные из JSON файла"""
    try:
        with open(file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        with InMemoryUnitOfWork() as uow:
            location_repo = uow.get_repository('location')
            hotel_repo = uow.get_repository('hotel')
            route_repo = uow.get_repository('route')
            
            # Импорт локаций
            location_map = {}
            if 'locations' in data:
                for loc_data in data['locations']:
                    location = Location(
                        name=loc_data['name'],
                        coordinates=Coordinates(loc_data['lat'], loc_data['lon']) if loc_data.get('lat') else None,
                        address=loc_data.get('address', ''),
                        city=loc_data.get('city', ''),
                        country=loc_data.get('country', '')
                    )
                    if loc_data.get('id'):
                        location.id = loc_data['id']
                    saved = location_repo.save(location)
                    location_map[loc_data['id']] = saved.id
            
            # Импорт отелей
            if 'hotels' in data:
                for hotel_data in data['hotels']:
                    location_id = location_map.get(hotel_data.get('location_id'))
                    location = location_repo.get_by_id(location_id) if location_id else None
                    
                    hotel = Hotel(
                        name=hotel_data['name'],
                        location=location,
                        rating=hotel_data.get('rating', 3.0),
                        price_per_night=hotel_data.get('price_per_night', 5000.0),
                        available_rooms=hotel_data.get('available_rooms', 10),
                        amenities=hotel_data.get('amenities', [])
                    )
                    if hotel_data.get('id'):
                        hotel.id = hotel_data['id']
                    hotel_repo.save(hotel)
            
            # Импорт маршрутов
            if 'routes' in data:
                for route_data in data['routes']:
                    segments = []
                    for seg_data in route_data.get('segments', []):
                        start = location_repo.get_by_id(seg_data.get('start_id'))
                        end = location_repo.get_by_id(seg_data.get('end_id'))
                        
                        if start and end:
                            transport = TransportType(seg_data.get('transport', 'car'))
                            segment = RouteSegment(
                                start=start,
                                end=end,
                                transport_type=transport,
                                distance_km=seg_data.get('distance', 0),
                                duration_min=seg_data.get('duration', 0)
                            )
                            segments.append(segment)
                    
                    if segments:
                        route = Route(segments=segments)
                        route.calculate_totals()
                        if route_data.get('id'):
                            route.id = route_data['id']
                        route_repo.save(route)
        
        print_success(f"Данные импортированы из {file}")
        
    except json.JSONDecodeError:
        print_error("Неверный формат JSON")
    except Exception as e:
        print_error(f"Ошибка при импорте: {e}")


@data.command('clear')
@click.confirmation_option(prompt="Вы уверены, что хотите удалить ВСЕ данные?")
def data_clear():
    """Очистить все данные"""
    try:
        # Очищаем репозитории
        location_repo._locations.clear()
        hotel_repo._hotels.clear()
        route_repo._routes.clear()
        
        # Сбрасываем счетчики ID
        location_repo._next_id = 1
        hotel_repo._next_id = 1
        route_repo._next_id = 1
        
        print_success("Все данные успешно удалены")
    except Exception as e:
        print_error(f"Ошибка при очистке: {e}")


# --- Демо команда ---

@cli.command()
def demo():
    """Загрузить демонстрационные данные"""
    print_info("Загрузка демонстрационных данных...")
    
    try:
        with InMemoryUnitOfWork() as uow:
            location_repo = uow.get_repository('location')
            hotel_repo = uow.get_repository('hotel')
            route_repo = uow.get_repository('route')
            
            # Создаем локации
            moscow = Location(
                name="Москва",
                coordinates=Coordinates(55.7558, 37.6173),
                address="Красная площадь, 1",
                city="Москва",
                country="Россия"
            )
            moscow = location_repo.save(moscow)
            
            spb = Location(
                name="Санкт-Петербург",
                coordinates=Coordinates(59.9343, 30.3351),
                address="Невский пр., 1",
                city="Санкт-Петербург",
                country="Россия"
            )
            spb = location_repo.save(spb)
            
            ekb = Location(
                name="Екатеринбург",
                coordinates=Coordinates(56.8389, 60.6057),
                address="ул. Ленина, 1",
                city="Екатеринбург",
                country="Россия"
            )
            ekb = location_repo.save(ekb)
            
            kazan = Location(
                name="Казань",
                coordinates=Coordinates(55.7887, 49.1221),
                address="Кремлевская ул., 1",
                city="Казань",
                country="Россия"
            )
            kazan = location_repo.save(kazan)
            
            # Создаем отели в Москве
            hotel1 = Hotel(
                name="Grand Hotel Moscow",
                location=moscow,
                rating=4.9,
                price_per_night=35000.0,
                available_rooms=20,
                amenities=["WiFi", "СПА", "Ресторан", "Бассейн"]
            )
            hotel1 = hotel_repo.save(hotel1)
            
            hotel2 = Hotel(
                name="Budget Inn Moscow",
                location=moscow,
                rating=3.2,
                price_per_night=2500.0,
                available_rooms=30,
                amenities=["WiFi", "Парковка"]
            )
            hotel2 = hotel_repo.save(hotel2)
            
            hotel3 = Hotel(
                name="Luxury Hotel Moscow",
                location=moscow,
                rating=4.8,
                price_per_night=45000.0,
                available_rooms=15,
                amenities=["WiFi", "СПА", "Ресторан", "Бассейн", "Терраса"]
            )
            hotel3 = hotel_repo.save(hotel3)
            
            # Создаем отели в Санкт-Петербурге
            hotel4 = Hotel(
                name="Hermitage Hotel",
                location=spb,
                rating=4.7,
                price_per_night=28000.0,
                available_rooms=25,
                amenities=["WiFi", "Ресторан", "Вид на Неву"]
            )
            hotel4 = hotel_repo.save(hotel4)
            
            hotel5 = Hotel(
                name="SPb Hostel",
                location=spb,
                rating=2.8,
                price_per_night=800.0,
                available_rooms=40,
                amenities=["WiFi", "Общая кухня"]
            )
            hotel5 = hotel_repo.save(hotel5)
            
            # Создаем маршрут Москва → СПб
            route1 = Route(segments=[
                RouteSegment(moscow, spb, TransportType.CAR)
            ])
            route1.calculate_totals()
            route1 = route_repo.save(route1)
            
            # Создаем маршрут Москва → Екатеринбург → СПб
            route2 = Route(segments=[
                RouteSegment(moscow, ekb, TransportType.TRAIN),
                RouteSegment(ekb, spb, TransportType.TRAIN)
            ])
            route2.calculate_totals()
            route2 = route_repo.save(route2)
            
            # Создаем маршрут с отелями
            route3 = Route(segments=[
                RouteSegment(moscow, hotel1.location, TransportType.CAR),
                RouteSegment(hotel1.location, hotel3.location, TransportType.CAR),
                RouteSegment(hotel3.location, spb, TransportType.CAR)
            ])
            route3.calculate_totals()
            route3 = route_repo.save(route3)
        
        print_success("Демонстрационные данные загружены!")
        print_info("Создано:")
        click.echo(f"  • Локаций: 4")
        click.echo(f"  • Отелей: 5")
        click.echo(f"  • Маршрутов: 3")
        
    except Exception as e:
        print_error(f"Ошибка при загрузке данных: {e}")


# --- Точка входа ---

if __name__ == '__main__':
    cli()