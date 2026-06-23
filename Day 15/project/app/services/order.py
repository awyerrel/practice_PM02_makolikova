from datetime import datetime, timedelta


def filter_and_sort_orders(orders):
    border_date = datetime.now() - timedelta(days=7)

    filtered = [
        order
        for order in orders
        if order["status"] != "CANCELLED"
        and order["date"] >= border_date
    ]

    return sorted(
        filtered,
        key=lambda x: x["total"],
        reverse=True
    )