"""`uvicorn deploy.gateway.main:app --host 0.0.0.0 --port $PORT` (the Dockerfile's CMD). Refuses to start when the settings leave a door open."""
from __future__ import annotations

import sys

from .app import create_app
from .config import Settings

_settings = Settings()
_problems = _settings.problems()
if _problems:
    sys.exit("The gateway will not start:\n- " + "\n- ".join(_problems))
app = create_app(_settings)
