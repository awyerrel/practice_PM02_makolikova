from src.booking import *

def test_cancel():
    bookings = {1: {"status": "active"}}
    result = cancel_booking(bookings, 1)
    assert result["status"] == "cancelled"