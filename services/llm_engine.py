import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_explanation(data, score, category, context):
    prompt = f"""
    You are a financial risk analyst.

    Customer Data:
    {data}

    Risk Score: {score}
    Category: {category}

    Context:
    {context}

    Explain:
    - Why this customer is risky
    - Key issues
    - Suggestions
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content