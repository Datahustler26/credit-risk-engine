from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from dotenv import load_dotenv
from models.schema import CustomerData

from services.rule_engine import calculate_risk, get_category
from services.rag_engine import get_context
from services.llm_engine import generate_explanation

load_dotenv()

app = FastAPI()

# ✅ Home route
@app.get("/", response_class=HTMLResponse)
def home():
    return """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Credit Risk Engine</title>
    <style>
      body { font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif; padding: 24px; }
      code { background: #f4f4f5; padding: 2px 6px; border-radius: 6px; }
      .box { max-width: 720px; margin: 0 auto; }
      a { color: #2563eb; text-decoration: none; }
      a:hover { text-decoration: underline; }
      .muted { color: #52525b; }
    </style>
  </head>
  <body>
    <div class="box">
      <h1>Credit Risk Engine</h1>
      <p class="muted">Backend is running. Use the API docs or call <code>POST /analyze</code>.</p>
      <ul>
        <li><a href="/docs">Swagger UI</a></li>
        <li><a href="/redoc">ReDoc</a></li>
        <li><a href="/health">Health</a></li>
      </ul>
    </div>
  </body>
</html>
""".strip()


@app.get("/health")
def health():
    return {"status": "ok"}

# ✅ Main API
@app.post("/analyze")
def analyze(data: CustomerData):
    try:
        data_dict = data.model_dump() if hasattr(data, "model_dump") else data.dict()

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
