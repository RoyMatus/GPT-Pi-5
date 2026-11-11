"""Public keyboard geometry only; never reads text or user input."""
import json
import math
import os
from pathlib import Path
import stat
import time


def read_geometry(path=None):
    hidden = {'visible': False, 'height': 0}
    if path is None:
        if os.name != 'posix':
            return hidden
        runtime = os.environ.get('XDG_RUNTIME_DIR', f'/run/user/{os.getuid()}')
        path = Path(runtime)/'gpt-pi-osk/geometry.json'
    try:
        with os.fdopen(os.open(path, os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0)
                              | getattr(os, 'O_NONBLOCK', 0)), 'rb') as source:
            mode = os.fstat(source.fileno())
            if not stat.S_ISREG(mode.st_mode) or mode.st_size > 256:
                return hidden
            if os.name == 'posix' and (mode.st_uid != os.getuid() or mode.st_mode & 0o077):
                return hidden
            data = json.loads(source.read(257))
        if not isinstance(data, dict):
            return hidden
        updated, height = data.get('updated'), data.get('height')
        if (type(updated) not in (int, float) or not math.isfinite(updated)
                or not 0 <= time.monotonic() - updated <= 3
                or type(height) is not int or not 0 <= height <= 8192
                or data.get('visible') is not True):
            return hidden
        return {'visible': True, 'height': height}
    except (OSError, ValueError, TypeError):
        return hidden
