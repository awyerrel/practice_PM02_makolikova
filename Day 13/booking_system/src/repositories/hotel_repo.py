from typing import List, Optional
from src.domain.models import Hotel
from src.repositories.base import BaseRepository


class HotelRepository(BaseRepository[Hotel]):
    """Репозиторий для работы с отелями (In-Memory)"""
    
    def __init__(self):
        self._storage: dict[int, Hotel] = {}
        self._next_id = 1
    
    def get_by_id(self, id: int) -> Optional[Hotel]:
        """Получить отель по ID"""
        return self._storage.get(id)
    
    def get_all(self, **filters) -> List[Hotel]:
        """Получить все отели с фильтрацией"""
        result = list(self._storage.values())
        
        if 'min_rating' in filters:
            result = [h for h in result if h.rating >= filters['min_rating']]
        
        if 'name' in filters:
            result = [h for h in result if filters['name'].lower() in h.name.lower()]
        
        if 'address' in filters:
            result = [h for h in result if filters['address'].lower() in h.address.lower()]
        
        return result
    
    def add(self, hotel: Hotel) -> Hotel:
        """Добавить новый отель"""
        hotel.id = self._next_id
        self._storage[hotel.id] = hotel
        self._next_id += 1
        return hotel
    
    def update(self, hotel: Hotel) -> Hotel:
        """Обновить отель"""
        if hotel.id not in self._storage:
            raise ValueError(f"Hotel with id {hotel.id} not found")
        self._storage[hotel.id] = hotel
        return hotel
    
    def delete(self, id: int) -> bool:
        """Удалить отель"""
        if id in self._storage:
            del self._storage[id]
            return True
        return False
    
    def get_by_rating_range(self, min_rating: float, max_rating: float) -> List[Hotel]:
        """Получить отели в диапазоне рейтинга"""
        result = []
        for hotel in self._storage.values():
            if min_rating <= hotel.rating <= max_rating:
                result.append(hotel)
        return result
    
    def get_top_rated(self, limit: int = 10) -> List[Hotel]:
        """Получить топ отелей по рейтингу"""
        sorted_hotels = sorted(
            self._storage.values(),
            key=lambda h: h.rating,
            reverse=True
        )
        return sorted_hotels[:limit]