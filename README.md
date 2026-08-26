# 🛡️ Archal Sandbox PoC: Deterministic Agent Evaluation

Standard AI observability (like Langfuse) fails because it only tests if the agent *thinks* it succeeded. To actually evaluate an agent, you need to execute it against a stateful clone and grade the backend database mutation.

This is a proof-of-concept demonstrating the core infrastructure required for deterministic agent evaluation, inspired by Archal (YC S26).

## 🎥 Demo

[Watch the PoC demo (Google Drive)](https://drive.google.com/file/d/1n0llHqOgpOV1Wu5XIrKlusZAUe0tauum/view?usp=sharing)

## 🏗️ Architecture

1. **The Stateful Clone (`fake_github.py`)**: A local FastAPI server mimicking the GitHub API. It maintains state in-memory.
2. **The TLS Intercept Sidecar (`traffic_cop.py`)**: A `mitmproxy` script that hijacks outbound HTTPS traffic to `api.github.com`, decrypts it using a custom CA, and seamlessly routes it to the local stateful clone.
3. **The Sandboxed Agent (`agent.py`)**: A standard AI agent using Groq and the official `requests` library. **Crucially, the base URL is NOT modified.** It connects to `https://api.github.com` but is transparently proxied to the clone.
4. **The Deterministic Grader (`evaluator.py`)**: Bypasses the proxy to read the backend memory of the Stateful Clone, mathematically proving the state mutation occurred.

## ▶️ Run the live demo

```powershell
cd D:\Codebase\Archal-Nano-Sandbox
$env:PYTHONIOENCODING = "utf-8"
py -m pip install fastapi uvicorn requests groq mitmproxy
py -u run_demo.py
```

Put a Groq key in `.env` as `GROQ_API_KEY=...`. The runner starts Fake City and Traffic Cop, executes the agent against `https://api.github.com`, then grades `/_internal/state` with no proxy.

## 👨‍💻 About

Built by Rafay Khattak, a CS grad from FAST NUCES specializing in systems engineering and agent infrastructure.
