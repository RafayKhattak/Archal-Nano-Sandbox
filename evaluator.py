import json
import sys

import requests

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

EXPECTED_REPO = "archal-labs/archal"
STATE_URL = "http://127.0.0.1:8000/_internal/state"


def fetch_internal_state() -> dict:
    session = requests.Session()
    session.trust_env = False
    response = session.get(STATE_URL, timeout=10)
    response.raise_for_status()
    return response.json()


def main() -> None:
    state = fetch_internal_state()
    starred = state.get("starred", [])

    if EXPECTED_REPO in starred:
        print(
            "✅ [EVALUATION PASSED] Deterministic State Check: "
            "'archal-labs/archal' was successfully starred in the backend database."
        )
    else:
        print(
            "❌ [EVALUATION FAILED] Agent hallucinated or failed. "
            "Expected state mutation not found in the backend database."
        )

    print(f"Raw internal state: {json.dumps(state, ensure_ascii=False)}")


if __name__ == "__main__":
    main()
