import pytest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import Base
from app.repositories import OrderRepository


@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        future=True,
    )

    Base.metadata.create_all(engine)

    SessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )

    session = SessionLocal()

    yield session

    session.close()
    Base.metadata.drop_all(engine)


@pytest.fixture
def repository(db_session):
    return OrderRepository(db_session)


@pytest.fixture
def order_data():
    return {
        "status": "PENDING",
        "customer_name": "Иван Иванов",
        "delivery_address": "Москва, ул. Ленина, 10",
        "total_amount": 4000.0,
        "items": [
            {
                "product_name": "Ноутбук",
                "quantity": 1,
                "price": 3000.0,
            },
            {
                "product_name": "Мышь",
                "quantity": 2,
                "price": 500.0,
            },
        ],
    }