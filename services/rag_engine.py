from pathlib import Path


def get_context() -> str:
    """
    Returns credit-risk policy context for the LLM step.

    Prefer loading from `data/policies.txt` so the context is editable without
    code changes. Falls back to a built-in policy summary if the file is missing.
    """
    # Use the file's own directory as the anchor instead of assuming depth
    policies_path = Path(__file__).resolve().parent.parent / "data" / "policies.txt"

    try:
        return policies_path.read_text(encoding="utf-8").strip()
    except OSError:
        return (
            "Credit Risk Policies:\n"
            "- Credit score below 600 is risky\n"
            "- High loan-to-income ratio increases risk\n"
            "- Multiple loans increase default probability\n"
            "- Late payments indicate risk\n"
        )