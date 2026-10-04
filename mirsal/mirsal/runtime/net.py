"""The names this machine answers to on the office network (docs/office_lan_plan.md 2.1): its LAN addresses, its host name, and MIRSAL_LAN_HOSTS
(comma-separated, for a DNS name the office uses). Nothing is sent: the UDP 'connect' only asks the operating system which interface would be used."""
from __future__ import annotations

import os
import socket


def lan_names() -> set[str]:
    names: set[str] = set()
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("10.255.255.255", 1))
        names.add(s.getsockname()[0])
        s.close()
    except OSError:
        pass
    try:
        names.update(socket.gethostbyname_ex(socket.gethostname())[2])
    except OSError:
        pass
    host = socket.gethostname().lower()
    names.update({host, host if host.endswith(".local") else host + ".local"})
    names.update(x.strip().lower() for x in os.environ.get("MIRSAL_LAN_HOSTS", "").split(",") if x.strip())
    names.discard("")
    return names
