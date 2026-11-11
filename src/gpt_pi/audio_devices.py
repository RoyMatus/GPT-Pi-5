"""Read audio availability without probing browser cameras or exposing device IDs."""
import asyncio
import json
import subprocess
import time


def classify(nodes):
    if not isinstance(nodes, list):
        raise ValueError('Invalid PipeWire state')
    classes = set()
    for node in nodes:
        if not isinstance(node, dict) or node.get('type') != 'PipeWire:Interface:Node':
            continue
        props = (node.get('info') or {}).get('props') or {}
        name = str(props.get('node.name', ''))
        if (name == 'auto_null' or name.endswith('.monitor')
                or props.get('factory.name') == 'support.null-audio-sink'):
            continue
        classes.add(props.get('media.class'))
    return {'microphone': 'Audio/Source' in classes, 'speaker': 'Audio/Sink' in classes}


def read_status():
    try:
        result = subprocess.run(['pw-dump', '-N'], capture_output=True, timeout=2,
                                check=True)
        if len(result.stdout) > 4_000_000:
            raise ValueError('Oversized PipeWire state')
        return classify(json.loads(result.stdout))
    except (OSError, subprocess.SubprocessError, ValueError, TypeError):
        # Unsupported platforms are unknown, not proof of absent hardware.
        return {'microphone': None, 'speaker': None}


class AudioDevices:
    def __init__(self):
        self.lock = asyncio.Lock()
        self.checked = None
        self.value = {'microphone': None, 'speaker': None}

    async def status(self):
        async with self.lock:
            if self.checked is None or time.monotonic() - self.checked >= 2:
                self.value = await asyncio.to_thread(read_status)
                self.checked = time.monotonic()
            return self.value.copy()
