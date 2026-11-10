"""Optional local speech engines. Audio stays in memory; cancellation kills the worker."""
import asyncio
import contextlib
import io
from pathlib import Path
import wave

MAX_AUDIO = 1_000_000
MAX_SPEECH_TEXT = 2500


class VoiceError(Exception):
    def __init__(self, code='voice_unavailable', status=503):
        self.code, self.status = code, status


def validate_audio(data):
    try:
        with wave.open(io.BytesIO(data), 'rb') as audio:
            frames = audio.getnframes()
            if (audio.getnchannels() != 1 or audio.getsampwidth() != 2
                    or audio.getframerate() != 16000 or audio.getcomptype() != 'NONE'
                    or not 1600 <= frames <= 480000
                    or len(audio.readframes(frames)) != frames * 2):
                raise ValueError()
    except (wave.Error, EOFError, ValueError):
        raise VoiceError('invalid_audio', 400) from None


class LocalVoice:
    def __init__(self, data_dir):
        self.root = Path(data_dir) / 'voice'
        self.python = self.root / 'venv/bin/python'
        self.lock = asyncio.Lock()

    def available(self):
        return all(path.is_file() for path in (
            self.python, self.root / 'vosk/am/final.mdl', self.root / 'ru.onnx',
            self.root / 'ru.onnx.json'))

    async def run(self, action, payload):
        if not self.available():
            raise VoiceError()
        if self.lock.locked():
            raise VoiceError('busy', 409)
        async with self.lock:
            process = None
            try:
                process = await asyncio.create_subprocess_exec(
                    str(self.python), '-I', str(Path(__file__).with_name('voice_worker.py')),
                    action, str(self.root), stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL,
                    env={'PATH': '/usr/bin:/bin', 'OMP_NUM_THREADS': '2',
                         'OPENBLAS_NUM_THREADS': '1', 'PYTHONDONTWRITEBYTECODE': '1'})
                async with asyncio.timeout(90):
                    output, _ = await process.communicate(payload)
                if process.returncode or not output or len(output) > 16_000_000:
                    raise VoiceError('voice_failed', 502)
                return output
            except TimeoutError:
                raise VoiceError('voice_timeout', 504) from None
            except OSError:
                raise VoiceError() from None
            finally:
                if process is not None and process.returncode is None:
                    with contextlib.suppress(ProcessLookupError):
                        process.kill()
                    await process.wait()

    async def transcribe(self, data):
        result = (await self.run('transcribe', data)).decode('utf-8').strip()
        if result == '-':
            raise VoiceError('speech_not_heard', 422)
        return result[:8000]

    async def speak(self, text):
        return await self.run('speak', text.encode('utf-8'))
