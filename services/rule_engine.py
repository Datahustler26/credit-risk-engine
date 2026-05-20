def calculate_risk(data: dict) -> int:
    score = 0

    income = float(data.get("income", 0) or 0)
    loan_amount = float(data.get("loan_amount", 0) or 0)
    credit_score = int(data.get("credit_score", 0) or 0)
    existing_loans = int(data.get("existing_loans", 0) or 0)
    late_payments = bool(data.get("late_payments", False))

    # Guard: only compute DTI when both values are present and non-zero
    if income > 0 and loan_amount > 0:
        dti = loan_amount / income
        if dti > 2:
            score += 40
    elif income == 0 and loan_amount > 0:
        # No income but loan requested — treat as maximum DTI risk
        score += 40

    if credit_score and credit_score < 600:
        score += 30

    if existing_loans > 2:
        score += 20

    if late_payments:
        score += 10

    return score


def get_category(score: int) -> str:
    if score >= 70:
        return "High Risk"
    elif score >= 40:
        return "Medium Risk"
    return "Low Risk"