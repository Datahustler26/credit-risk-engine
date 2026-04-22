from pydantic import BaseModel

class CustomerData(BaseModel):
    income: float
    loan_amount: float
    credit_score: int
    existing_loans: int
    late_payments: bool