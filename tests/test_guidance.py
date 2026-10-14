from pathlib import Path
import tempfile
import unittest

from tools.check_guidance import validate


class GuidanceTests(unittest.TestCase):
    def test_repository_guidance_is_resolvable(self):
        self.assertEqual([], validate(Path(__file__).resolve().parents[1]))

    def test_missing_guidance_is_reported(self):
        with tempfile.TemporaryDirectory() as temp:
            self.assertTrue(validate(Path(temp)))
