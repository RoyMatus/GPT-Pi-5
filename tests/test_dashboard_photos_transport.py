import io,stat,tempfile,unittest
from contextlib import contextmanager
from types import SimpleNamespace
from PIL import Image
from gpt_pi.dashboard.photos.service import Photos
from gpt_pi.dashboard.ssh.service import SourceError
class FakeFile(io.BytesIO):
 def stat(self):return ATTR
_buffer=io.BytesIO();Image.new('RGB',(4,2),'red').save(_buffer,'JPEG');DATA=_buffer.getvalue()
ATTR=SimpleNamespace(st_mode=stat.S_IFREG|0o444,st_size=len(DATA),st_mtime=1)
class FakeSFTP:
 def normalize(self,path):return path
 def lstat(self,path):return ATTR
 def listdir_iter(self,root,read_aheads=1):
  return iter([SimpleNamespace(filename='../escape.jpg'),SimpleNamespace(filename='safe.jpg'),SimpleNamespace(filename='link.jpg')])
 def open(self,path,mode):
  assert path=='/photos/safe.jpg' and mode=='rb'
  image=Image.new('RGB',(4,2),'red');data=io.BytesIO();image.save(data,'JPEG');return FakeFile(data.getvalue())
class FakeState:
 generation=1
 @contextmanager
 def sftp(self,session,grant):
  if session.dashboard.get('photoGrant') is not grant or grant['generation']!=self.generation:raise SourceError('permission_denied')
  sftp=FakeSFTP()
  original=sftp.lstat;sftp.lstat=lambda path:SimpleNamespace(st_mode=stat.S_IFLNK,st_size=10,st_mtime=1) if path.endswith('link.jpg') else original(path)
  yield sftp
class PhotoTransportTests(unittest.IsolatedAsyncioTestCase):
 async def test_listing_rejects_links_and_traversal_then_reads_only_registered_id(self):
  state=FakeState();service=Photos(SimpleNamespace(state=lambda session:state));session=SimpleNamespace(alive=True,dashboard={'photoGrant':{'root':'/photos','generation':1}},resources=set(),dashboard_tasks=set())
  result=await service.listing(session);self.assertEqual([f['name'] for f in result['files']],['safe.jpg'])
  with self.assertRaises(SourceError):await service.image(session,'/photos/safe.jpg')
  data=await service.image(session,result['files'][0]['id']);self.assertEqual(Image.open(io.BytesIO(data)).size,(4,2))
  state.generation=2
  with self.assertRaises(SourceError):await service.image(session,result['files'][0]['id'])
