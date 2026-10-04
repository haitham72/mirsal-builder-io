"""Container entry point: starts the engine and the gateway (MODE=web) or the worker (MODE=worker) and exits as soon as any child dies, so the platform restarts the box.
Stdlib only. The engine listens on loopback; only the gateway's port is exposed."""
from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.request


def main() -> int:
    mode = os.environ.get("MODE", "web").lower()
    py = sys.executable
    procs: list[subprocess.Popen] = []
    if mode == "worker":
        procs.append(subprocess.Popen([py, "-m", "mirsal", "worker"], cwd="mirsal"))
    else:
        port = os.environ.get("PORT", "8080")
        procs.append(subprocess.Popen([py, "-m", "mirsal", "serve", "--port", "8789"], cwd="mirsal"))
        for _ in range(60):                                       # the gateway does not start before the engine answers
            try:
                urllib.request.urlopen("http://127.0.0.1:8789/api/health", timeout=1).read()
                break
            except urllib.error.HTTPError:
                break                                             # a 401 is an ANSWER: with the gateway secret set the engine wants an identity, and it is up
            except Exception:
                time.sleep(1)
        else:
            print("the engine did not come up in 60 seconds", file=sys.stderr)
            procs[0].terminate()
            return 1
        # the platform's proxy is the only thing that can reach this port: trust its X-Forwarded-* (an env var, not an argument: a "*" argument is glob-expanded by the Windows C runtime)
        procs.append(subprocess.Popen([py, "-m", "uvicorn", "deploy.gateway.main:app", "--host", "0.0.0.0", "--port", port, "--proxy-headers"], env=dict(os.environ, FORWARDED_ALLOW_IPS="*")))

    def stop(*_):
        for p in procs:
            p.terminate()
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    while all(p.poll() is None for p in procs):
        time.sleep(1)
    stop()
    return next((p.returncode for p in procs if p.returncode), 1)


if __name__ == "__main__":
    sys.exit(main())
