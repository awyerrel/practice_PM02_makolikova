from src.hotel import *

def test_hotels():
    hotels = [{"rating":5},{"rating":3}]
    result = get_top_hotels(hotels)
    assert len(result) == 1