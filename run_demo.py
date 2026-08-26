"""Live end-to-end demo: Fake City + Traffic Cop + Agent + Evaluator.

Recording:
  py -u run_demo.py

Quick check (almost no pauses):
  py -u run_demo.py --fast
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PYTHON = sys.executable

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass


def banner(title: str) -> None:
    line = "=" * 72
    print(f"\n{line}\n  {title}\n{line}", flush=True)


def pause(seconds: float, fast: bool) -> None:
    time.sleep(0.4 if fast else seconds)


def free_port(port: int) -> None:
    result = subprocess.run(
        ["netstat", "-ano"],
        capture_output=True,
        text=True,
        check=False,
    )
    pattern = re.compile(rf":{port}\s+.*LISTENING\s+(\d+)", re.IGNORECASE)
    pids: set[str] = set()
    for line in result.stdout.splitlines():
        match = pattern.search(line)
        if match:
            pids.add(match.group(1))
    for pid in pids:
        subprocess.run(
            ["taskkill", "/F", "/PID", pid],
            capture_output=True,
            check=False,
        )


def find_mitmdump() -> str:
    found = shutil.which("mitmdump")
    if found:
        return found
    sibling = Path(PYTHON).with_name("mitmdump.exe")
    if sibling.exists():
        return str(sibling)
    scripts = Path(PYTHON).parent / "Scripts" / "mitmdump.exe"
    if scripts.exists():
        return str(scripts)
    raise FileNotFoundError("mitmdump.exe not found. Install with: py -m pip install mitmproxy")


def pump_output(prefix: str, proc: subprocess.Popen[str]) -> None:
    assert proc.stdout is not None
    for line in iter(proc.stdout.readline, ""):
        print(f"{prefix} {line}", end="", flush=True)


def wait_for_port(port: int, proc: subprocess.Popen[str], timeout: float = 25) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if proc.poll() is not None:
            raise RuntimeError(f"Process on port {port} exited with code {proc.returncode}")
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(0.4)
            if sock.connect_ex(("127.0.0.1", port)) == 0:
                return
        time.sleep(0.2)
    raise RuntimeError(f"Port {port} did not open in time.")


def start_service(
    prefix: str,
    args: list[str],
    ready_port: int,
    extra_env: dict[str, str] | None = None,
) -> subprocess.Popen[str]:
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUNBUFFERED"] = "1"
    if extra_env:
        env.update(extra_env)
    proc = subprocess.Popen(
        args,
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        bufsize=1,
    )
    threading.Thread(target=pump_output, args=(prefix, proc), daemon=True).start()
    wait_for_port(ready_port, proc)
    return proc


def run_step(title: str, args: list[str]) -> None:
    banner(title)
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUNBUFFERED"] = "1"
    completed = subprocess.run(
        args,
        cwd=ROOT,
        env=env,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(f"{title} exited with code {completed.returncode}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fast", action="store_true", help="Skip recording pauses")
    args = parser.parse_args()
    fast = args.fast

    os.chdir(ROOT)
    banner("Starting Fake City :8000 and Traffic Cop :8080")
    pause(10, fast)
    free_port(8000)
    free_port(8080)
    time.sleep(1)

    fake_city = start_service(
        "[FAKE CITY]",
        [PYTHON, "fake_github.py"],
        8000,
    )
    traffic_cop = start_service(
        "[TRAFFIC COP]",
        [
            find_mitmdump(),
            "-s",
            "traffic_cop.py",
            "--listen-port",
            "8080",
            "--set",
            "connection_strategy=lazy",
        ],
        8080,
    )
    pause(12, fast)

    banner("agent.py")
    pause(8, fast)
    run_step("agent.py", [PYTHON, "-u", "agent.py"])
    pause(8, fast)

    banner("evaluator.py")
    pause(4, fast)
    run_step("evaluator.py", [PYTHON, "-u", "evaluator.py"])
    pause(14, fast)

    print("\nPress Enter to stop servers.", flush=True)
    if fast:
        time.sleep(0.5)
    else:
        try:
            input()
        except EOFError:
            time.sleep(3)

    for proc in (traffic_cop, fake_city):
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted.", flush=True)
        sys.exit(1)
