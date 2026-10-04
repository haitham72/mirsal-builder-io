"""Free text that may leave this machine (a ticket, an error answer, a console line) never carries where the machine keeps its files."""
from __future__ import annotations

import re

_WIN_PATH = re.compile(r"(?<!\w)[A-Za-z]:[\\/](?:[^\\/\s'\"<>|:*?]+[\\/])*([^\\/\s'\"<>|:*?]*)")
_POSIX_PATH = re.compile(r"(?<![\w.:/])/(?:Users|home|tmp|var|private|mnt|opt|root|Volumes|srv)/(?:[^/\s'\"<>|]+/)*([^/\s'\"<>|]*)")


def scrub_paths(text: str) -> str:
    """An absolute file path in free text (an exception message, a log line) becomes `<path>/name`: where a machine keeps its files never leaves it,
    the file name stays so the message is still readable. Relative paths and URL paths are left alone."""
    return _POSIX_PATH.sub(r"<path>/\1", _WIN_PATH.sub(r"<path>/\1", text))
