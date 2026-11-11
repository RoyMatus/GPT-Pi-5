"""The transferable design must reject changed or missing frozen bytes."""
import tempfile
import unittest
from pathlib import Path

from tools.package_theme_resources import checked_bytes, safe_name, write_archive


class ThemeResourceTests(unittest.TestCase):
    def test_rejects_changed_or_missing_reference(self):
        with tempfile.TemporaryDirectory() as directory:
            file = Path(directory) / "preview.png"
            file.write_bytes(b"approved")
            import hashlib
            digest = hashlib.sha256(b"approved").hexdigest()
            self.assertEqual(checked_bytes(file, digest), b"approved")
            file.write_bytes(b"redesigned")
            with self.assertRaisesRegex(ValueError, "Checksum"):
                checked_bytes(file, digest)
            file.unlink()
            with self.assertRaises(FileNotFoundError):
                checked_bytes(file, digest)

    def test_rejects_unsafe_archive_paths(self):
        for name in ("../preview.png", "/absolute", "C:/file", "a\\b", "a/../../b"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                safe_name(name)
        self.assertEqual(safe_name("source/frontend/appearance.css"), "source/frontend/appearance.css")

    def test_archive_is_repeatable_and_preserves_bytes(self):
        import zipfile
        with tempfile.TemporaryDirectory() as directory:
            first, second = Path(directory) / "a.zip", Path(directory) / "b.zip"
            entries = {"previews/reference.png": b"PNG bytes", "source/app.css": b"exact\n"}
            write_archive(first, entries)
            write_archive(second, dict(reversed(list(entries.items()))))
            self.assertEqual(first.read_bytes(), second.read_bytes())
            with zipfile.ZipFile(first) as archive:
                for name, content in entries.items():
                    self.assertEqual(archive.read(name), content)


if __name__ == "__main__":
    unittest.main()
