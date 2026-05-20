import os
from typing import Any
from pathlib import Path

# ── Thresholds ──────────────────────────────────────────────────────────────
DTI_THRESHOLD = 2.0
MIN_CREDIT_SCORE = 600
MAX_EXISTING_LOANS = 2

# ── Internal helpers ─────────────────────────────────────────────────────────

def _extract_risk_factors(data: dict[str, Any]) -> list[str]:
    """
    Pure factor-extraction logic; returns a list of human-readable risk factors.
    Separated from prose formatting so it can be unit-tested independently.
    """
    income = float(data.get("income", 0) or 0)
    loan_amount = float(data.get("loan_amount", 0) or 0)
    credit_score = int(data.get("credit_score", 0) or 0)
    existing_loans = int(data.get("existing_loans", 0) or 0)
    late_payments = bool(data.get("late_payments", False))

    factors: list[str] = []

    # Only flag DTI when there is an actual loan being requested
    if income > 0 and loan_amount > 0 and (loan_amount / income) > DTI_THRESHOLD:
        factors.append("high debt-to-income ratio")
    elif income == 0 and loan_amount > 0:
        factors.append("no reported income against a loan request")

    if credit_score and credit_score < MIN_CREDIT_SCORE:
        factors.append("low credit score")
    if existing_loans > MAX_EXISTING_LOANS:
        factors.append("multiple existing loans")
    if late_payments:
        factors.append("history of late payments")

    return factors


def _suggestion_for_category(category: str) -> str:
    suggestions = {
        "Low Risk": "Customer appears low risk; proceed with standard underwriting checks.",
        "Medium Risk": "Consider tighter terms, additional verification, or a smaller exposure.",
    }
    return suggestions.get(
        category,
        "Consider reducing loan amount, improving credit score, and lowering outstanding debt.",
    )


def _fallback_explanation(
    data: dict[str, Any],
    score: int,
    category: str,
    *,
    prefix: str = "Rule-based assessment",
) -> str:
    """
    Construct a plain-text explanation using only rule-based logic.

    Args:
        data: Raw customer feature dict.
        score: Numeric risk score.
        category: Risk category label (e.g. "Low Risk").
        prefix: Opening label, overridable so callers can signal LLM fallback.
    """
    factors = _extract_risk_factors(data)
    factors_text = ", ".join(factors) if factors else "no major rule-based red flags detected"
    suggestion = _suggestion_for_category(category)

    return (
        f"{prefix}: {category} (score {score}). "
        f"Key factors: {factors_text}. "
        f"Suggestion: {suggestion}"
    )


def _load_api_key_from_env_file() -> str | None:
    """
    Backward-compatible: reads OPENAI_API_KEY from a repo-root .env file.
    Supports both `OPENAI_API_KEY=sk-…` and bare `sk-…` lines (legacy format).
    Returns the key string, or None if not found / file missing.
    """
    repo_root = Path(__file__).resolve().parents[1]
    env_path = repo_root / ".env"
    try:
        for raw_line in env_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("OPENAI_API_KEY="):
                value = line.split("=", 1)[1].strip().strip('"').strip("'")
                return value or None
            # Legacy bare-key format: entire line is the key (no `=` present at all)
            if "=" not in line and line.startswith("sk-"):
                return line
    except OSError:
        pass
    return None


def _format_customer_data(data: dict[str, Any]) -> str:
    """Render customer data as stable key: value lines rather than raw dict repr."""
    return "\n".join(f"  {k}: {v}" for k, v in sorted(data.items()))


# ── Public API ───────────────────────────────────────────────────────────────

def generate_explanation(
    data: dict[str, Any],
    score: int,
    category: str,
    context: str,
) -> str:
    """
    Generate a natural-language risk explanation for a loan applicant.

    Tries the OpenAI API first; falls back to rule-based logic if the key is
    absent, the SDK is not installed, or the network call fails.

    Args:
        data: Raw customer feature dict (income, credit_score, …).
        score: Numeric risk score produced by the scoring model.
        category: Human-readable risk category ("Low Risk", "Medium Risk", …).
        context: Additional context string forwarded to the LLM prompt.

    Returns:
        A human-readable explanation string.
    """
    api_key = os.getenv("OPENAI_API_KEY") or _load_api_key_from_env_file()

    if not api_key:
        return _fallback_explanation(data, score, category)

    try:
        from openai import OpenAI  # type: ignore
    except ImportError:
        return (
            "LLM unavailable (openai package not installed; using rule-based fallback). "
            + _fallback_explanation(data, score, category)
        )

    prompt = f"""
You are a financial risk analyst.

Customer Data:
{_format_customer_data(data)}

Risk Score: {score}
Category: {category}

Context:
{context}

Please explain:
- Why this customer is considered risky (or not)
- The key issues driving this assessment
- Concrete suggestions for the underwriter
""".strip()

    try:
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
        )

        choice = response.choices[0]
        if not choice.message.content:
            reason = choice.finish_reason  # e.g. "content_filter", "tool_calls", "stop"
            return (
                f"LLM returned no content (finish_reason={reason!r}; using rule-based fallback). "
                + _fallback_explanation(data, score, category)
            )

        return choice.message.content

    except Exception as e:
        # Surface the error type so callers/logs know what went wrong,
        # then degrade gracefully rather than raising.
        return (
            f"LLM unavailable ({type(e).__name__}; using rule-based fallback). "
            + _fallback_explanation(data, score, category)
        )