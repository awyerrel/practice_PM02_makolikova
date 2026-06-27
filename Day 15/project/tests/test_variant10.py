from datetime import datetime, timedelta
from app.services.order import filter_and_sort_orders


def test_filter_and_sort_orders():
    today = datetime.now()

    orders = [
        {
            "date": today - timedelta(days=3),
            "total": 100,
            "status": "PAID"
        },
        {
            "date": today - timedelta(days=10),
            "total": 200,
            "status": "PAID"
        },
        {
            "date": today - timedelta(days=1),
            "total": 50,
            "status": "CANCELLED"
        },
        {
            "date": today - timedelta(days=2),
            "total": 300,
            "status": "PAID"
        },
        {
            "date": today - timedelta(days=7),
            "total": 150,
            "status": "PAID"
        }
    ]

    result = filter_and_sort_orders(orders)

    assert len(result) == 3
    assert result[0]["total"] == 300
    assert result[1]["total"] == 150
    assert result[2]["total"] == 100