import pytest
from src.dto.hotel_dto import HotelCreateDTO, HotelUpdateDTO, HotelSearchDTO
from src.domain.exceptions import HotelNotFoundError, DomainError


class TestHotelService:
    """Тесты для HotelService"""
    
    def test_create_hotel_success(self, hotel_service):
        """Тест успешного создания отеля"""
        dto = HotelCreateDTO(
            name="Test Hotel",
            address="123 Test St",
            phone="+1-555-000-0000",
            rating=4.0
        )
        
        result = hotel_service.create(dto)
        
        assert result.id is not None
        assert result.name == "Test Hotel"
        assert result.rating == 4.0
    
    def test_create_hotel_duplicate_name(self, hotel_service):
        """Тест ошибки при создании отеля с существующим именем"""
        dto1 = HotelCreateDTO(
            name="Unique Hotel",
            address="123 St",
            phone="+1-555-000-0000",
            rating=4.0
        )
        hotel_service.create(dto1)
        
        dto2 = HotelCreateDTO(
            name="Unique Hotel",
            address="456 St",
            phone="+1-555-111-1111",
            rating=3.5
        )
        
        with pytest.raises(DomainError) as exc_info:
            hotel_service.create(dto2)
        
        assert "already exists" in str(exc_info.value)
    
    def test_get_hotel_by_id_success(self, hotel_service):
        """Тест получения отеля по ID"""
        dto = HotelCreateDTO(
            name="Test Hotel",
            address="123 Test St",
            phone="+1-555-000-0000",
            rating=4.0
        )
        created = hotel_service.create(dto)
        
        result = hotel_service.get_by_id(created.id)
        
        assert result.id == created.id
        assert result.name == "Test Hotel"
    
    def test_get_hotel_by_id_not_found(self, hotel_service):
        """Тест ошибки получения несуществующего отеля"""
        with pytest.raises(HotelNotFoundError):
            hotel_service.get_by_id(999)
    
    def test_update_hotel_success(self, hotel_service):
        """Тест успешного обновления отеля"""
        dto = HotelCreateDTO(
            name="Test Hotel",
            address="123 Test St",
            phone="+1-555-000-0000",
            rating=4.0
        )
        created = hotel_service.create(dto)
        
        update_dto = HotelUpdateDTO(
            name="Updated Hotel",
            rating=4.8
        )
        
        result = hotel_service.update(created.id, update_dto)
        
        assert result.name == "Updated Hotel"
        assert result.rating == 4.8
    
    def test_get_all_hotels(self, hotel_service):
        """Тест получения всех отелей"""
        dto1 = HotelCreateDTO(name="Hotel 1", address="St 1", phone="111", rating=4.0)
        dto2 = HotelCreateDTO(name="Hotel 2", address="St 2", phone="222", rating=4.5)
        
        hotel_service.create(dto1)
        hotel_service.create(dto2)
        
        results = hotel_service.get_all()
        
        assert len(results) >= 2
    
    def test_get_top_rated(self, hotel_service):
        """Тест получения топ отелей"""
        dto1 = HotelCreateDTO(name="Hotel 1", address="St 1", phone="111", rating=3.0)
        dto2 = HotelCreateDTO(name="Hotel 2", address="St 2", phone="222", rating=4.5)
        dto3 = HotelCreateDTO(name="Hotel 3", address="St 3", phone="333", rating=5.0)
        
        hotel_service.create(dto1)
        hotel_service.create(dto2)
        hotel_service.create(dto3)
        
        results = hotel_service.get_top_rated(limit=2)
        
        assert len(results) == 2
        assert results[0].rating >= results[1].rating
    
    def test_update_rating(self, hotel_service):
        """Тест обновления рейтинга"""
        dto = HotelCreateDTO(
            name="Test Hotel",
            address="123 St",
            phone="111",
            rating=3.0
        )
        created = hotel_service.create(dto)
        
        result = hotel_service.update_rating(created.id, 4.7)
        
        assert result.rating == 4.7
    
    def test_search_by_name(self, hotel_service):
        """Тест поиска отелей по названию"""
        dto = HotelCreateDTO(
            name="Grand Palace Hotel",
            address="123 St",
            phone="111",
            rating=4.0
        )
        hotel_service.create(dto)
        
        results = hotel_service.search_by_name("Palace")
        
        assert len(results) > 0
        assert "Palace" in results[0].name