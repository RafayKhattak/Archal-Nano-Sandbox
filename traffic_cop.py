import sys

import mitmproxy.http

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


class TrafficCop:
    def request(self, flow: mitmproxy.http.HTTPFlow) -> None:
        if flow.request.pretty_host == "api.github.com":
            flow.request.host = "127.0.0.1"
            flow.request.port = 8000
            flow.request.scheme = "http"
            print(
                f"🚨 [TRAFFIC COP] Intercepted {flow.request.method} {flow.request.path} -> Rerouted to Fake City!",
                flush=True,
            )


addons = [TrafficCop()]
