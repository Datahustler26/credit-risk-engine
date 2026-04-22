from fastapi import FastAPI
from pydantic import BaseModel

from services.rule_engine import calculate_risk, get_category
from services.rag_engine import get_context
from services.llm_engine import generate_explanation

app = FastAPI()

# ✅ Schema
class CustomerData(BaseModel):
    income: float
    loan_amount: float
    credit_score: int
    existing_loans: int
    late_payments: bool

# ✅ Home route
@app.get("/")
def home():
    return {"message": "AI Risk Intelligence API is running 🚀"}

# ✅ Main API
@app.post("/analyze")
def analyze(data: CustomerData):
    try:
        data_dict = data.dict()   # 🔥 IMPORTANT FIX

        score = calculate_risk(data_dict)
        category = get_category(score)

        context = get_context()

        explanation = generate_explanation(
            data_dict, score, category, context
        )

        return {
            "risk_score": score,
            "risk_category": category,
            "llm_explanation": explanation
        }

    except Exception as e:
        return {"error": str(e)}