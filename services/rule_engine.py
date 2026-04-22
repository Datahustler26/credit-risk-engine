def calculate_risk(data):
    score = 0

    dti = data["loan_amount"] / data["income"]

    if dti > 2:
        score += 40

    if data["credit_score"] < 600:
        score += 30

    if data["existing_loans"] > 2:
        score += 20

    if data["late_payments"]:
        score += 10

    return score


def get_category(score):
    if score >= 70:
        return "High Risk"
    elif score >= 40:
        return "Medium Risk"
    return "Low Risk"