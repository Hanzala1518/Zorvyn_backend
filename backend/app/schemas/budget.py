from pydantic import BaseModel
from decimal import Decimal
from typing import Optional


class BudgetCreate(BaseModel):
    category: str
    monthly_limit: Decimal


class BudgetUpdate(BaseModel):
    monthly_limit: Optional[Decimal] = None
    is_active: Optional[bool] = None


class BudgetResponse(BaseModel):
    id: str
    category: str
    monthly_limit: float
    spent_this_month: float
    remaining: float
    percentage_used: float
    status: str