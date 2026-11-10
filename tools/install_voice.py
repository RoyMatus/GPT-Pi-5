"""Install optional Russian speech locally on Linux. No sudo or service changes."""
import argparse
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import venv
import zipfile

REVISION = 'cf910fb59f1d79ab3b625a63993a108751c6c25d'
VOICE_URL = f'https://huggingface.co/rhasspy/piper-voices/resolve/{REVISION}/ru/ru_RU/denis/medium/'
ASSETS = {
    'vosk-model-small-ru-0.22.zip': (
        'https://alphacephei.com/vosk/models/vosk-model-small-ru-0.22.zip',
        '961d5ff98a17f4aa6de69864d0aa71fa5bac682301d2b5d17a3f24c5c99a46d4'),
    'ru_RU-denis-medium.onnx': (VOICE_URL + 'ru_RU-denis-medium.onnx',
        '879bc365cb14d1380e3f5ed6044162ccf54c99f6161871569b7f830aec3ce841'),
    'ru_RU-denis-medium.onnx.json': (VOICE_URL + 'ru_RU-denis-medium.onnx.json',
        'e4fb4ab60262d1ab802c8c39301976c4135e545bc834a33c6eedc1f764df3bd6'),
    'MODEL_CARD': (VOICE_URL + 'MODEL_CARD',
        '917110d5056810771fd3daea2644bbadf1341816b7631f2043b33be245903432'),
}


def verified_asset(name, cache):
    url, digest = ASSETS[name]
    path = cache / name
    if not path.exists():
        temp = path.with_suffix(path.suffix + '.download')
        try:
            with urllib.request.urlopen(url, timeout=30) as source, temp.open('wb') as output:
                total = 0
                while chunk := source.read(1024 * 1024):
                    total += len(chunk)
                    if total > 80_000_000:
                        raise ValueError('download limit')
                    output.write(chunk)
            if hashlib.sha256(temp.read_bytes()).hexdigest() != digest:
                raise ValueError('asset checksum mismatch')
            temp.replace(path)
        finally:
            temp.unlink(missing_ok=True)
    if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
        raise ValueError('asset checksum mismatch: ' + name)
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir', type=Path, default=Path(os.environ.get('GPT_PI_DATA_DIR') or
                        Path(os.environ.get('XDG_DATA_HOME') or Path.home() / '.local/share') / 'gpt-pi'))
    parser.add_argument('--assets-dir', type=Path)
    args = parser.parse_args()
    if sys.platform != 'linux':
        parser.error('Run this installer on the Linux device')
    root = args.data_dir.expanduser().resolve() / 'voice'
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    cache = (args.assets_dir or root / 'downloads').resolve()
    cache.mkdir(parents=True, exist_ok=True)
    assets = {name: verified_asset(name, cache) for name in ASSETS}
    if not (root / 'vosk').exists():
        with tempfile.TemporaryDirectory(dir=root) as directory:
            target = Path(directory).resolve()
            with zipfile.ZipFile(assets['vosk-model-small-ru-0.22.zip']) as archive:
                for item in archive.infolist():
                    if not (target / item.filename).resolve().is_relative_to(target):
                        raise ValueError('unsafe model archive')
                archive.extractall(target)
            (target / 'vosk-model-small-ru-0.22').rename(root / 'vosk')
    for source, name in [('ru_RU-denis-medium.onnx', 'ru.onnx'),
                         ('ru_RU-denis-medium.onnx.json', 'ru.onnx.json'),
                         ('MODEL_CARD', 'VOICE_MODEL_CARD')]:
        shutil.copyfile(assets[source], root / name)
    python = root / 'venv/bin/python'
    if not python.exists():
        venv.EnvBuilder(with_pip=True).create(root / 'venv')
    environment = {**os.environ, 'PIP_CONFIG_FILE': os.devnull}
    subprocess.run([str(python), '-m', 'pip', 'install', '--index-url', 'https://pypi.org/simple',
                    '--timeout', '30', '--retries', '2', 'vosk==0.3.45', 'piper-tts==1.8.0'],
                   env=environment, check=True, timeout=600)
    subprocess.run([str(python), '-c', 'import vosk; from piper import PiperVoice'], check=True)
    print('Local Russian speech engines installed. Microphone and speaker still require a device check.')


if __name__ == '__main__':
    main()
