"""Read-only, bounded local probe. No installation, recording, SSH or secret reads."""
import argparse
import ctypes
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess


def linux_memory(text):
    data = {}
    for line in text.splitlines():
        parts = line.split()
        if parts and parts[0] in {"MemTotal:", "MemAvailable:"} and len(parts) >= 3 and parts[2] == "kB":
            data[parts[0][:-1]] = int(parts[1]) * 1024
    return {"total_bytes": data.get("MemTotal"), "available_bytes": data.get("MemAvailable")}


def memory():
    if platform.system() == "Linux":
        try:
            return linux_memory(Path('/proc/meminfo').read_text())
        except (OSError, ValueError):
            pass
    if platform.system() == "Windows":
        class Status(ctypes.Structure):
            _fields_ = [("length", ctypes.c_ulong), ("load", ctypes.c_ulong)] + [
                (name, ctypes.c_ulonglong) for name in
                ("total", "available", "page_total", "page_available", "virtual_total", "virtual_available", "extended")]
        status = Status()
        status.length = ctypes.sizeof(status)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
            return {"total_bytes": status.total, "available_bytes": status.available}
    return {"total_bytes": None, "available_bytes": None}


def probe(command):
    if shutil.which(command[0]) is None:
        return {"status": "unavailable"}
    try:
        result = subprocess.run(command, capture_output=True, text=True,
                                encoding="utf-8", errors="replace", timeout=5)
        return {"status": "ok" if result.returncode == 0 else "failed",
                "output": result.stdout[:4000] if result.returncode == 0 else ""}
    except subprocess.TimeoutExpired:
        return {"status": "timeout"}
    except OSError:
        return {"status": "unavailable"}


def collect(device=False):
    system = platform.system()
    result = {"system": system, "architecture": platform.machine(),
              "python": platform.python_version(), "logical_cpus": os.cpu_count(),
              "workspace_free_bytes": shutil.disk_usage(Path.cwd()).free,
              "memory": memory(),
              "tools": {name: shutil.which(name) is not None for name in
                        ('git', 'systemctl', 'chromium', 'chromium-browser', 'aplay', 'arecord', 'wpctl')},
              "hardware_verified": False}
    if device:
        if system != "Linux":
            result["device"] = {"status": "unsupported_host"}
        else:
            session = os.environ.get("XDG_SESSION_TYPE", "unknown")
            result["device"] = {"session_type": session if session in {'x11', 'wayland', 'tty'} else 'unknown',
                                "capture": probe(['arecord', '-l']),
                                "playback": probe(['aplay', '-l']),
                                "pipewire": probe(['wpctl', 'status'])}
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--device', action='store_true')
    args = parser.parse_args()
    print(json.dumps(collect(args.device), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
