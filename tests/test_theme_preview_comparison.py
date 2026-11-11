"""A changed pixel or screenshot size cannot silently pass visual acceptance."""
import unittest
from PIL import Image
from tools.compare_theme_previews import changed_pixels


class PreviewComparisonTests(unittest.TestCase):
    def test_identical_and_single_pixel_change(self):
        reference = Image.new("RGB", (3, 2), "white")
        actual = reference.copy()
        self.assertEqual(changed_pixels(reference, actual), 0)
        actual.putpixel((1, 1), (254, 255, 255))
        self.assertEqual(changed_pixels(reference, actual), 1)

    def test_different_size_cannot_match(self):
        with self.assertRaisesRegex(ValueError, "size"):
            changed_pixels(Image.new("RGB", (2, 2)), Image.new("RGB", (3, 2)))


if __name__ == "__main__":
    unittest.main()
