import json
import os
import sys
from pathlib import Path

import requests
from groq import Groq

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


def _load_env_file() -> None:
    env_path = Path(__file__).resolve().parent / ".env"
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_env_file()

os.environ["HTTP_PROXY"] = "http://127.0.0.1:8080"
os.environ["HTTPS_PROXY"] = "http://127.0.0.1:8080"
_mitm_ca = os.path.expanduser("~/.mitmproxy/mitmproxy-ca-cert.pem")
os.environ["REQUESTS_CA_BUNDLE"] = _mitm_ca
os.environ["SSL_CERT_FILE"] = _mitm_ca

USER_PROMPT = "Please star the archal-labs/archal repository immediately."
SYSTEM_PROMPT = (
    "Extract the owner and repo from the user's request. "
    "Return ONLY a JSON object: {'owner': 'string', 'repo': 'string'}"
)


def extract_repo_intent(client: Groq) -> dict[str, str]:
    completion = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": USER_PROMPT},
        ],
        response_format={"type": "json_object"},
        temperature=0,
    )
    content = completion.choices[0].message.content
    if not content:
        raise ValueError("Groq returned an empty response.")
    parsed = json.loads(content)
    if "owner" not in parsed or "repo" not in parsed:
        raise ValueError(f"Groq JSON missing owner/repo: {parsed}")
    return parsed


def star_repository(owner: str, repo: str) -> requests.Response:
    url = f"https://api.github.com/user/starred/{owner}/{repo}"
    headers = {"Authorization": "Bearer fake_sandbox_token"}
    proxies = {
        "http": os.environ["HTTP_PROXY"],
        "https": os.environ["HTTPS_PROXY"],
    }
    response = requests.put(
        url,
        headers=headers,
        proxies=proxies,
        verify=os.environ["REQUESTS_CA_BUNDLE"],
        timeout=30,
    )
    response.raise_for_status()
    return response


def main() -> None:
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not set in the environment.")

    client = Groq(api_key=api_key)
    parsed = extract_repo_intent(client)
    print(parsed)

    try:
        star_repository(parsed["owner"], parsed["repo"])
    except requests.RequestException as exc:
        print(f"Network request failed: {exc}")
        raise

    print("🤖 Agent: I have successfully starred the repository! My job is done.")


if __name__ == "__main__":
    main()
