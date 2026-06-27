from datetime import datetime

import pytest
from sqlalchemy import select

from app.exceptions import (
    DeliveryCalculationException,
    EntityNotFoundException,
)
from app.models import Order, OrderItem


def test_create_order(repository, db_session, order_data):
    order = repository.create(order_data)

    assert order.id is not None
    assert order.customer_name == "Иван Иванов"
    assert order.status == "PENDING"
    assert len(order.items) == 2

    saved = db_session.get(Order, order.id)

    assert saved is not None
    assert len(saved.items) == 2
    assert saved.total_amount == 4000.0


def test_find_existing_order(repository, order_data):
    created = repository.create(order_data)

    found = repository.find_by_id(created.id)

    assert found is not None
    assert found.id == created.id
    assert found.customer_name == created.customer_name


def test_find_non_existing_order(repository):
    assert repository.find_by_id(9999) is None


@pytest.mark.parametrize(
    "status",
    [
        "PENDING",
        "PAID",
        "SHIPPED",
        "CANCELLED",
    ],
)
def test_find_all_by_status(repository, order_data, status):
    order_data["status"] = status
    repository.create(order_data)

    other = {
        **order_data,
        "status": "PENDING" if status != "PENDING" else "PAID",
    }

    repository.create(other)

    result = repository.find_all_by_status(status)

    assert len(result) == 1
    assert result[0].status == status


def test_update_status(repository, order_data):
    order = repository.create(order_data)

    repository.update_status(order.id, "PAID")

    updated = repository.find_by_id(order.id)

    assert updated.status == "PAID"


def test_update_status_not_found(repository):
    with pytest.raises(EntityNotFoundException):
        repository.update_status(999, "PAID")


def test_delete_order(repository, order_data):
    order = repository.create(order_data)

    repository.delete(order.id)

    assert repository.find_by_id(order.id) is None


def test_delete_order_items(repository, db_session, order_data):
    order = repository.create(order_data)

    repository.delete(order.id)

    items = (
        db_session.query(OrderItem)
        .filter(OrderItem.order_id == order.id)
        .all()
    )

    assert items == []


def test_delete_not_existing(repository):
    with pytest.raises(EntityNotFoundException):
        repository.delete(12345)


def test_find_by_date_range(repository, db_session, order_data):
    order1 = repository.create(order_data)

    order2 = repository.create({
        **order_data,
        "customer_name": "Петр Петров",
    })

    order3 = repository.create({
        **order_data,
        "customer_name": "Сергей Сергеев",
    })

    order1.created_at = datetime(2024, 1, 1)
    order2.created_at = datetime(2024, 1, 15)
    order3.created_at = datetime(2024, 2, 1)

    db_session.commit()

    result = repository.find_by_date_range(
        datetime(2024, 1, 1),
        datetime(2024, 1, 31),
    )

    assert len(result) == 2

    names = {order.customer_name for order in result}

    assert "Иван Иванов" in names
    assert "Петр Петров" in names


def test_get_total_amount(repository, order_data):
    order = repository.create(order_data)

    total = repository.get_total_amount_for_order(order.id)

    expected = (
        1 * 3000.0 +
        2 * 500.0
    )

    assert total == expected


def test_create_order_transaction_rollback(
    repository,
    db_session,
    order_data,
):
    invalid_order = {
        **order_data,
        "items": [
            {
                "product_name": "Ноутбук",
                "quantity": -1,
                "price": 3000.0,
            }
        ],
    }

    with pytest.raises(ValueError):
        repository.create(invalid_order)

    orders = db_session.scalars(select(Order)).all()

    assert len(orders) == 0



# Контрактные тесты


def test_calculate_delivery_success(
    repository,
    order_data,
    httpx_mock,
):
    order = repository.create(order_data)

    httpx_mock.add_response(
        method="POST",
        url="https://api.delivery.com/calculate",
        json={
            "cost": 150.0
        },
        status_code=200,
    )

    cost = repository.calculate_delivery_cost(order.id)

    assert cost == 150.0

    request = httpx_mock.get_requests()[0]

    assert str(request.url) == "https://api.delivery.com/calculate"

    body = request.read().decode()

    assert "Москва" in body
    assert "weight" in body


def test_calculate_delivery_server_error(
    repository,
    order_data,
    httpx_mock,
):
    order = repository.create(order_data)

    httpx_mock.add_response(
        method="POST",
        url="https://api.delivery.com/calculate",
        status_code=500,
    )

    with pytest.raises(DeliveryCalculationException):
        repository.calculate_delivery_cost(order.id)