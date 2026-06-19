import pytest
import os
import json
import tracemalloc
from src.variant_10 import FileProcessor, results_cache, create_test_data


class TestFileProcessor:
    """Тесты для FileProcessor"""
    
    @pytest.fixture
    def setup_processor(self):
        """Создание процессора с тестовыми данными"""
        filename = create_test_data()
        processor = FileProcessor(filename)
        processor.load_data()
        return processor
    
    def test_load_data(self, setup_processor):
        """Тест загрузки данных"""
        assert len(setup_processor.data) > 0
        assert setup_processor.data[0]['name'] == 'Alice'
        assert setup_processor.data[0]['age'] == 25
        assert setup_processor.data[0]['score'] == 85.5
    
    def test_process_data(self, setup_processor):
        """Тест обработки данных"""
        setup_processor.process_data()
        assert len(results_cache) > 0
        assert results_cache[0]['name'] == 'Alice'
        assert 'bonus' in results_cache[0]
        assert 'ratio' in results_cache[0]
    
    def test_calculate_statistics(self, setup_processor):
        """Тест расчета статистики"""
        stats = setup_processor.calculate_statistics()
        assert stats['count'] > 0
        assert stats['avg_score'] > 0
        assert isinstance(stats['avg_score'], float)
    
    def test_division_by_zero(self, setup_processor):
        """Тест защиты от деления на ноль"""
        setup_processor.process_data()
        # Проверяем, что нет записей с бесконечностью
        for item in results_cache:
            assert item['ratio'] != float('inf')
            assert item['ratio'] != float('-inf')
    
    def test_save_results(self, setup_processor, tmp_path):
        """Тест сохранения результатов"""
        output_file = tmp_path / "test_results.json"
        setup_processor.process_data()
        setup_processor.save_results(str(output_file))
        
        assert os.path.exists(output_file)
        with open(output_file, 'r') as f:
            data = json.load(f)
            assert 'total_processed' in data
            assert 'results' in data
            assert len(data['results']) > 0
    
    def test_file_not_found(self):
        """Тест обработки отсутствующего файла"""
        processor = FileProcessor("nonexistent.csv")
        with pytest.raises(FileNotFoundError):
            processor.load_data()
    
    def test_empty_file(self, tmp_path):
        """Тест обработки пустого файла"""
        empty_file = tmp_path / "empty.csv"
        empty_file.write_text("")
        
        processor = FileProcessor(str(empty_file))
        with pytest.raises(ValueError):
            processor.load_data()
    
    def test_invalid_data(self, tmp_path):
        """Тест обработки невалидных данных"""
        invalid_file = tmp_path / "invalid.csv"
        invalid_file.write_text("Name,Age,Score\nTest,-5,150\n")
        
        processor = FileProcessor(str(invalid_file))
        processor.load_data()
        assert len(processor.data) == 0  # Невалидные данные пропущены


class TestMemory:
    """Тесты для проверки памяти"""
    
    def test_memory_leak(self):
        """Тест отсутствия утечек памяти"""
        tracemalloc.start()
        initial = tracemalloc.take_snapshot()
        
        # Очищаем кеш перед тестом
        results_cache.clear()
        
        # Многократная обработка данных
        for _ in range(10):
            filename = create_test_data()
            processor = FileProcessor(filename)
            processor.load_data()
            processor.process_data()
            results_cache.clear()
        
        final = tracemalloc.take_snapshot()
        diff = final.compare_to(initial, 'lineno')
        
        # Проверяем, что память не растет значительно
        total_diff = sum(stat.size_diff for stat in diff)
        assert total_diff < 1024 * 1024  # Меньше 1MB
    
    def test_cache_limit(self):
        """Тест ограничения кеша"""
        global results_cache
        results_cache = []
        
        filename = create_test_data()
        processor = FileProcessor(filename)
        processor.load_data()
        
        # Обрабатываем данные несколько раз
        for _ in range(3):
            processor.process_data()
        
        # Проверяем, что кеш ограничен
        assert len(results_cache) <= 1000  # CACHE_MAX_SIZE


class TestEdgeCases:
    """Тесты для краевых случаев"""
    
    def test_large_number_of_records(self, tmp_path):
        """Тест с большим количеством записей"""
        # Создаем файл с 100 записями
        large_file = tmp_path / "large.csv"
        with open(large_file, 'w') as f:
            f.write("Name,Age,Score\n")
            for i in range(100):
                f.write(f"User{i},{20 + i % 10},{50 + i % 50}\n")
        
        processor = FileProcessor(str(large_file))
        processor.load_data()
        assert len(processor.data) == 100
        
        processor.process_data()
        assert len(results_cache) <= 1000
    
    def test_special_characters_in_names(self, tmp_path):
        """Тест с специальными символами в именах"""
        special_file = tmp_path / "special.csv"
        special_file.write_text("Name,Age,Score\nJohn Doe,25,85.5\nMaria-Garcia,30,90.0\n")
        
        processor = FileProcessor(str(special_file))
        processor.load_data()
        assert processor.data[0]['name'] == 'John Doe'
        assert processor.data[1]['name'] == 'Maria-Garcia'
    
    def test_float_scores(self, tmp_path):
        """Тест с дробными значениями"""
        float_file = tmp_path / "float.csv"
        float_file.write_text("Name,Age,Score\nTest1,25,85.55\nTest2,30,90.75\n")
        
        processor = FileProcessor(str(float_file))
        processor.load_data()
        assert processor.data[0]['score'] == 85.55
        assert processor.data[1]['score'] == 90.75


if __name__ == "__main__":
    pytest.main([__file__, "-v"])