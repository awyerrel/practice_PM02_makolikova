from typing import List, Optional
from src.domain.models import Hotel
from src.domain.exceptions import HotelNotFoundError, DomainError
from src.dto.hotel_dto import HotelCreateDTO, HotelResponseDTO, HotelUpdateDTO, HotelSearchDTO
from src.uow.unit_of_work import UnitOfWork


class HotelService:
    """Сервис для управления отелями"""
    
    def __init__(self, uow: UnitOfWork):
        self.uow = uow
        self.hotel_repo = uow.hotels
    
    def create(self, dto: HotelCreateDTO) -> HotelResponseDTO:
        """
        Создать новый отель.
        
        Args:
            dto: Данные для создания отеля
            
        Returns:
            HotelResponseDTO: Созданный отель
            
        Raises:
            DomainError: Если отель с таким именем уже существует
        """
        # Проверяем, нет ли отеля с таким именем
        existing = self.hotel_repo.get_all(name=dto.name)
        if existing:
            raise DomainError(
                f"Hotel with name '{dto.name}' already exists",
                {"name": dto.name}
            )
        
        # Создаем отель
        hotel = Hotel(
            id=None,
            name=dto.name,
            address=dto.address,
            phone=dto.phone,
            rating=dto.rating
        )
        
        saved = self.hotel_repo.add(hotel)
        self.uow.commit()
        
        return HotelResponseDTO.from_hotel(saved)
    
    def get_by_id(self, hotel_id: int) -> HotelResponseDTO:
        """
        Получить отель по ID.
        
        Args:
            hotel_id: ID отеля
            
        Returns:
            HotelResponseDTO: Найденный отель
            
        Raises:
            HotelNotFoundError: Если отель не найден
        """
        hotel = self.hotel_repo.get_by_id(hotel_id)
        if not hotel:
            raise HotelNotFoundError(hotel_id)
        return HotelResponseDTO.from_hotel(hotel)
    
    def get_all(self, search_dto: Optional[HotelSearchDTO] = None) -> List[HotelResponseDTO]:
        """
        Получить все отели с фильтрацией.
        
        Args:
            search_dto: Параметры поиска
            
        Returns:
            List[HotelResponseDTO]: Список отелей
        """
        filters = {}
        if search_dto:
            if search_dto.name:
                filters['name'] = search_dto.name
            if search_dto.min_rating is not None:
                filters['min_rating'] = search_dto.min_rating
        
        hotels = self.hotel_repo.get_all(**filters)
        
        # Дополнительная фильтрация по max_rating
        if search_dto and search_dto.max_rating is not None:
            hotels = [h for h in hotels if h.rating <= search_dto.max_rating]
        
        return [HotelResponseDTO.from_hotel(h) for h in hotels]
    
    def update(self, hotel_id: int, dto: HotelUpdateDTO) -> HotelResponseDTO:
        """
        Обновить отель.
        
        Args:
            hotel_id: ID отеля
            dto: Данные для обновления
            
        Returns:
            HotelResponseDTO: Обновленный отель
            
        Raises:
            HotelNotFoundError: Если отель не найден
        """
        hotel = self.hotel_repo.get_by_id(hotel_id)
        if not hotel:
            raise HotelNotFoundError(hotel_id)
        
        # Обновляем только переданные поля
        if dto.name is not None:
            hotel.name = dto.name
        if dto.address is not None:
            hotel.address = dto.address
        if dto.phone is not None:
            hotel.phone = dto.phone
        if dto.rating is not None:
            hotel.rating = dto.rating
        
        updated = self.hotel_repo.update(hotel)
        self.uow.commit()
        
        return HotelResponseDTO.from_hotel(updated)
    
    def delete(self, hotel_id: int) -> bool:
        """
        Удалить отель.
        
        Args:
            hotel_id: ID отеля
            
        Returns:
            bool: True если удаление успешно
            
        Raises:
            HotelNotFoundError: Если отель не найден
            DomainError: Если в отеле есть активные номера
        """
        hotel = self.hotel_repo.get_by_id(hotel_id)
        if not hotel:
            raise HotelNotFoundError(hotel_id)
        
        # Проверяем, есть ли в отеле номера
        rooms = self.uow.rooms.get_by_hotel(hotel_id, active_only=False)
        if rooms:
            raise DomainError(
                f"Cannot delete hotel with {len(rooms)} rooms. Delete rooms first.",
                {"hotel_id": hotel_id, "rooms_count": len(rooms)}
            )
        
        result = self.hotel_repo.delete(hotel_id)
        self.uow.commit()
        return result
    
    def update_rating(self, hotel_id: int, rating: float) -> HotelResponseDTO:
        """
        Обновить рейтинг отеля.
        
        Args:
            hotel_id: ID отеля
            rating: Новый рейтинг
            
        Returns:
            HotelResponseDTO: Обновленный отель
            
        Raises:
            HotelNotFoundError: Если отель не найден
        """
        hotel = self.hotel_repo.get_by_id(hotel_id)
        if not hotel:
            raise HotelNotFoundError(hotel_id)
        
        hotel.rating = rating
        updated = self.hotel_repo.update(hotel)
        self.uow.commit()
        
        return HotelResponseDTO.from_hotel(updated)
    
    def get_top_rated(self, limit: int = 10) -> List[HotelResponseDTO]:
        """
        Получить топ отелей по рейтингу.
        
        Args:
            limit: Количество отелей
            
        Returns:
            List[HotelResponseDTO]: Список отелей
        """
        hotels = self.hotel_repo.get_top_rated(limit)
        return [HotelResponseDTO.from_hotel(h) for h in hotels]
    
    def search_by_name(self, name: str) -> List[HotelResponseDTO]:
        """
        Поиск отелей по названию.
        
        Args:
            name: Часть названия
            
        Returns:
            List[HotelResponseDTO]: Список найденных отелей
        """
        hotels = self.hotel_repo.get_all(name=name)
        return [HotelResponseDTO.from_hotel(h) for h in hotels]