import io,unittest
from PIL import Image
from gpt_pi.dashboard.photos.service import safe_join,decode_image
class PhotoTests(unittest.TestCase):
 def test_paths_cannot_escape_or_be_substituted(self):
  for name in ['../secret.jpg','/secret.jpg','C:/secret.jpg','a/b.jpg','a\\b.jpg','..']:
   with self.assertRaises(ValueError):safe_join('/photos',name)
  self.assertEqual(safe_join('/photos','Снимок 1.jpg'),'/photos/Снимок 1.jpg')
 def test_exif_rotation_metadata_removal_and_pixel_bound(self):
  image=Image.new('RGB',(4,2),'blue');exif=Image.Exif();exif[274]=6;source=io.BytesIO();image.save(source,'JPEG',exif=exif)
  result=Image.open(io.BytesIO(decode_image(source.getvalue())))
  self.assertEqual(result.size,(2,4));self.assertFalse(result.getexif())
  with self.assertRaises(ValueError):decode_image(source.getvalue(),pixel_limit=4)
