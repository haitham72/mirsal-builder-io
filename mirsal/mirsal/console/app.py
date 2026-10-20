"""Compatibility entry point. HTTP implementation lives in mirsal.api."""
from ..api.app import Server, create_app, quiet_loop  # noqa: F401
