from datetime import datetime

import httpx
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.exceptions import (
    DeliveryCalculationException,
    EntityNotFoundException,
)
from app.models import Order, OrderItem


class OrderRepository:
    DELIVERY_URL = "https://api.delivery.com/calculate"

    def __init__(self, session: Session):
        self.session = session

    def create(self, order_data: dict) -> Order:
        try:
            order = Order(
                status=order_data["status"],
                customer_name=order_data["customer_name"],
                delivery_address=order_data["delivery_address"],
                total_amount=order_data["total_amount"],
            )

            for item in order_data.get("items", []):
                if item["quantity"] < 0:
                    raise ValueError("Quantity cannot be negative")

                order.items.append(
                    OrderItem(
                        product_name=item["product_name"],
                        quantity=item["quantity"],
                        price=item["price"],
                    )
                )

            self.session.add(order)
            self.session.commit()
            self.session.refresh(order)

            return order

        except Exception:
            self.session.rollback()
            raise

    def find_by_id(self, order_id: int):
        return self.session.get(Order, order_id)

    def find_all_by_status(self, status: str):
        stmt = select(Order).where(Order.status == status)
        return list(self.session.scalars(stmt).all())

    def update_status(self, order_id: int, new_status: str):
        order = self.find_by_id(order_id)

        if order is None:
            raise EntityNotFoundException(
                f"Order {order_id} not found"
            )

        order.status = new_status

        self.session.commit()
        self.session.refresh(order)

        return order

    def delete(self, order_id: int):
        order = self.find_by_id(order_id)

        if order is None:
            raise EntityNotFoundException(
                f"Order {order_id} not found"
            )

        self.session.delete(order)
        self.session.commit()

    def find_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
    ):
        stmt = (
            select(Order)
            .where(Order.created_at >= start_date)
            .where(Order.created_at <= end_date)
        )

        return list(self.session.scalars(stmt).all())

    def get_total_amount_for_order(
        self,
        order_id: int,
    ) -> float:
        stmt = (
            select(
                func.sum(
                    OrderItem.quantity * OrderItem.price
                )
            )
            .where(OrderItem.order_id == order_id)
        )

        total = self.session.scalar(stmt)

        return float(total or 0)

    def calculate_delivery_cost(
        self,
        order_id: int,
    ) -> float:
        order = self.find_by_id(order_id)

        if order is None:
            raise EntityNotFoundException(
                f"Order {order_id} not found"
            )

        weight = sum(
            item.quantity * 0.5
            for item in order.items
        )

        response = httpx.post(
            self.DELIVERY_URL,
            json={
                "address": order.delivery_address,
                "weight": weight,
            },
        )

        if response.status_code >= 400:
            raise DeliveryCalculationException(
                "Delivery service unavailable"
            )

        return response.json()["cost"]