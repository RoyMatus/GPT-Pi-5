"""Fail a release build clearly when the locally bundled UI is missing."""
from pathlib import Path
from setuptools import setup
from setuptools.command.build_py import build_py


class BuildWithInterface(build_py):
    def run(self):
        for name in ('app.js', 'app.css'):
            if not Path('src/gpt_pi/web/assets', name).is_file():
                raise RuntimeError('Build Fluent 2 first: npm ci && npm run build')
        super().run()


setup(cmdclass={'build_py': BuildWithInterface})
