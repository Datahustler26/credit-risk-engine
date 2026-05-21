from pydantic import BaseModel
from typing import Optional

class CustomerData(BaseModel):
    income: float
    loan_amount: float
    credit_score: int
    existing_loans: int
    late_payments: bool
    financial_report: Optional[str] = None