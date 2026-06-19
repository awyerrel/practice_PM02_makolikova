import pytest
from datetime import datetime, timedelta
from src.fake_validator import FakeValidator

class TestProperties:
    def test_simple(self):
        assert 1 + 1 == 2