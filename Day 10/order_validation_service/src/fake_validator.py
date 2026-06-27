from datetime import datetime
from typing import Dict, Any, Optional, List
import random
from pydantic import BaseModel
from enum import Enum

class Category(str, Enum):
    FOOD = "Food"
    ALCOHOL = "Alcohol"

class Item(BaseModel):
    product_id: str
    quantity: int
    price: float
    category: Category

class OrderInput(BaseModel):
    order_id: str
    user_id: str
    items: List[Item] = []
    total_amount: float
    order_time: datetime
    created_at: Optional[datetime] = None
    age_verified: bool = False
    email_changed_at: Optional[datetime] = None
    delivery_country: str
    wallet_country: Optional[str] = None

class FakeValidator:
    def __init__(self, chaos_mode: bool = False, delay_seconds: float = 0.0):
        self.chaos_mode = chaos_mode
        self.delay_seconds = delay_seconds

    def validate_order(self, order: Dict[str, Any]) -> Dict[str, Any]:
        if self.chaos_mode and random.random() < 0.05:
            return {"valid": False, "reasons": ["Chaos"], "risk_score": 0.5}

        try:
            validated_order = OrderInput(**order)
        except Exception:
            return {"valid": False, "reasons": ["Invalid input"], "risk_score": 0.0}

        reasons = []

        if not (0 < validated_order.total_amount < 1000000):
            reasons.append("Order amount must be between 0 and 1,000,000")

        risk_score = 0.0
        if validated_order.total_amount > 100000:
            risk_score = 0.9

        return {
            "valid": len(reasons) == 0,
            "reasons": reasons,
            "risk_score": risk_score
        }