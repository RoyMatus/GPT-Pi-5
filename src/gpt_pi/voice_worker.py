"""Run inside the optional voice venv. Fixed local models, stdin/stdout only."""
import io
import json
from pathlib import Path
import sys
import wave


def main():
    action, directory = sys.argv[1:]
    root = Path(directory)
    payload = sys.stdin.buffer.read(1_000_001)
    if len(payload) > 1_000_000:
        raise ValueError('input limit')
    if action == 'transcribe':
        from vosk import KaldiRecognizer, Model, SetLogLevel
        SetLogLevel(-1)
        model = Model(str(root / 'vosk'))
        recognizer = KaldiRecognizer(model, 16000)
        parts = []
        with wave.open(io.BytesIO(payload), 'rb') as audio:
            while chunk := audio.readframes(4000):
                if recognizer.AcceptWaveform(chunk):
                    parts.append(json.loads(recognizer.Result()).get('text', ''))
        parts.append(json.loads(recognizer.FinalResult()).get('text', ''))
        sys.stdout.buffer.write((' '.join(parts).strip() or '-').encode('utf-8'))
    elif action == 'speak':
        from piper import PiperVoice
        text = payload.decode('utf-8')
        if not 1 <= len(text) <= 2500:
            raise ValueError('text limit')
        voice = PiperVoice.load(str(root / 'ru.onnx'))
        output = io.BytesIO()
        with wave.open(output, 'wb') as audio:
            voice.synthesize_wav(text, audio)
        sys.stdout.buffer.write(output.getvalue())
    else:
        raise ValueError('unknown action')


if __name__ == '__main__':
    main()
