from typing import List, Optional
from src.domain.models import Room
from src.repositories.base import BaseRepository


class RoomRepository(BaseRepository[Room]):
    """Репозиторий для работы с номерами (In-Memory)"""
    
    def __init__(self):
        self._storage: dict[int, Room] = {}
        self._next_id = 1
    
    def get_by_id(self, id: int) -> Optional[Room]:
        """Получить номер по ID"""
        return self._storage.get(id)
    
    def get_all(self, **filters) -> List[Room]:
        """Получить все номера с фильтрацией"""
        result = list(self._storage.values())
        
        if 'hotel_id' in filters:
            result = [r for r in result if r.hotel_id == filters['hotel_id']]
        
        if 'is_active' in filters:
            result = [r for r in result if r.is_active == filters['is_active']]
        
        if 'min_capacity' in filters:
            result = [r for r in result if r.capacity >= filters['min_capacity']]
        
        if 'room_type' in filters:
            result = [r for r in result if r.room_type == filters['room_type']]
        
        if 'max_price' in filters:
            result = [r for r in result if r.price_per_night <= filters['max_price']]
        
        return result
    
    def add(self, room: Room) -> Room:
        """Добавить новый номер"""
        room.id = self._next_id
        self._storage[room.id] = room
        self._next_id += 1
        return room
    
    def update(self, room: Room) -> Room:
        """Обновить номер"""
        if room.id not in self._storage:
            raise ValueError(f"Room with id {room.id} not found")
        self._storage[room.id] = room
        return room
    
    def delete(self, id: int) -> bool:
        """Удалить номер"""
        if id in self._storage:
            del self._storage[id]
            return True
        return False
    
    def get_by_hotel(self, hotel_id: int, active_only: bool = True) -> List[Room]:
        """Получить все номера отеля"""
        result = [r for r in self._storage.values() if r.hotel_id == hotel_id]
        if active_only:
            result = [r for r in result if r.is_active]
        return result
    
    def get_by_type(self, room_type: str, active_only: bool = True) -> List[Room]:
        """Получить номера по типу"""
        result = [r for r in self._storage.values() if r.room_type == room_type]
        if active_only:
            result = [r for r in result if r.is_active]
        return result
    
    def get_available_rooms(self, hotel_id: int, capacity: Optional[int] = None) -> List[Room]:
        """Получить доступные активные номера отеля"""
        rooms = self.get_by_hotel(hotel_id, active_only=True)
        if capacity:
            rooms = [r for r in rooms if r.capacity >= capacity]
        return rooms