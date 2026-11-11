"""Read-only SFTP photo operations, session grants, bounded decoding, no disk cache."""
import asyncio,io,posixpath,stat,time
from uuid import uuid4
from PIL import Image,ImageOps,UnidentifiedImageError
from ..ssh.service import SourceError
MAX_BYTES=8*1024*1024
EXTENSIONS={'.jpg','.jpeg','.png','.webp'}

def canonical(path):
 path=path.replace('\\','/')
 if len(path)>3 and path[0]=='/' and path[2]==':':path=path[1:]
 return posixpath.normpath(path)

def safe_join(root,name):
 if not isinstance(name,str) or not 1<=len(name)<=255 or name in ['.','..'] or any(c in name for c in ['/', '\\', ':','\0']) or any(ord(c)<32 for c in name):raise ValueError('invalid_path')
 return posixpath.join(root,name)

def checked_path(sftp,root,name):
 path=safe_join(root,name)
 if canonical(sftp.normalize(root))!=canonical(root) or canonical(sftp.normalize(path))!=canonical(path):raise ValueError('path_changed')
 attributes=sftp.lstat(path)
 if not attributes.st_mode or not stat.S_ISREG(attributes.st_mode) or type(attributes.st_size)!=int or not 0<attributes.st_size<=MAX_BYTES:raise ValueError('invalid_file')
 return path,attributes

def signature(attributes):return attributes.st_mode,attributes.st_size,attributes.st_mtime

def decode_image(data,pixel_limit=12000000):
 if not 0<len(data)<=MAX_BYTES:raise ValueError('image_limit')
 try:
  with Image.open(io.BytesIO(data)) as image:
   if image.format not in ['JPEG','PNG','WEBP'] or image.width*image.height>pixel_limit:raise ValueError('image_limit')
   image=ImageOps.exif_transpose(image).convert('RGB');image.thumbnail((1920,1920),Image.Resampling.LANCZOS)
   output=io.BytesIO();image.save(output,'JPEG',quality=85,exif=b'')
   if output.tell()>2*1024*1024:output=io.BytesIO();image.save(output,'JPEG',quality=65,exif=b'')
   if output.tell()>2*1024*1024:raise ValueError('image_limit')
   return output.getvalue()
 except (OSError,UnidentifiedImageError,Image.DecompressionBombError) as exc:raise ValueError('invalid_image') from None

def clear_photos(session):
 session.dashboard.pop('photoGrant',None);session.dashboard.pop('photoFiles',None)
 for resource in list(session.resources):resource.close()

class Photos:
 def __init__(self,computer):self.computer=computer;self.semaphore=asyncio.Semaphore(1)
 async def run(self,session,worker):
  task=asyncio.current_task();session.dashboard_tasks.add(task)
  try:
   await self.semaphore.acquire()
   worker_task=asyncio.create_task(asyncio.to_thread(worker))
   def finished(task):
    self.semaphore.release()
    if not task.cancelled():task.exception()
   worker_task.add_done_callback(finished)
   return await asyncio.wait_for(asyncio.shield(worker_task),20)
  except (asyncio.CancelledError,TimeoutError):
   for resource in list(session.resources):resource.close()
   raise
  finally:session.dashboard_tasks.discard(task)
 async def configure(self,session,data):
  if set(data)!={'root','confirmed','serverRestricted'} or data['confirmed'] is not True or data['serverRestricted'] is not True:raise ValueError('photo_permission')
  root=data['root']
  if not isinstance(root,str) or not 1<=len(root)<=1024 or any(ord(c)<32 for c in root) or '..' in root.replace('\\','/').split('/'):raise ValueError('invalid_path')
  root=root.replace('\\','/')
  if not root.startswith('/') and not (len(root)>2 and root[1:3]==':/'):raise ValueError('invalid_path')
  state=self.computer.state(session);mark=state.generation;clear_photos(session)
  def check():
   with state.connect(session,photo=True) as client:
    sftp=client.open_sftp();sftp.get_channel().settimeout(8)
    try:
     resolved=sftp.normalize(root)
     if canonical(resolved)!=canonical(root):raise ValueError('symlink_root')
     if not stat.S_ISDIR(sftp.lstat(resolved).st_mode or 0):raise ValueError('invalid_root')
     return resolved
    finally:sftp.close()
  resolved=await self.run(session,check)
  if not session.alive or state.generation!=mark:raise SourceError('permission_denied')
  session.dashboard['photoGrant']={'root':resolved,'generation':mark,'token':uuid4().hex};session.dashboard['photoFiles']={}
 async def listing(self,session):
  state=self.computer.state(session);grant=session.dashboard.get('photoGrant')
  if not grant:return {'state':'not_configured','files':[]}
  if grant['generation']!=state.generation:clear_photos(session);return {'state':'permission_denied','files':[]}
  old={entry['path']:identifier for identifier,entry in session.dashboard.get('photoFiles',{}).items()}
  def scan():
   files={};truncated=False;deadline=time.monotonic()+12
   with state.sftp(session,grant) as sftp:
    for count,item in enumerate(sftp.listdir_iter(grant['root'],read_aheads=1)):
     if time.monotonic()>deadline:raise SourceError('timeout')
     if count>=512:truncated=True;break
     if posixpath.splitext(item.filename)[1].lower() not in EXTENSIONS:continue
     try:path,attributes=checked_path(sftp,grant['root'],item.filename)
     except ValueError:continue
     identifier=old.get(path) or uuid4().hex;files[identifier]={'path':path,'name':item.filename,'signature':signature(attributes)}
   return files,truncated
  files,truncated=await self.run(session,scan)
  if not session.alive or session.dashboard.get('photoGrant') is not grant or state.generation!=grant['generation']:raise SourceError('permission_denied')
  session.dashboard['photoFiles']=files
  return {'state':'ready','files':sorted([{'id':key,'name':value['name']} for key,value in files.items()],key=lambda x:x['name'].casefold()),'truncated':truncated}
 async def image(self,session,identifier):
  state=self.computer.state(session);grant=session.dashboard.get('photoGrant');entry=session.dashboard.get('photoFiles',{}).get(identifier)
  if not grant or not entry:raise SourceError('not_found')
  def read():
   with state.sftp(session,grant) as sftp:
    path,attributes=checked_path(sftp,grant['root'],entry['name'])
    if signature(attributes)!=entry['signature']:raise ValueError('file_changed')
    with sftp.open(path,'rb') as handle:
     if signature(handle.stat())!=entry['signature']:raise ValueError('file_changed')
     data=handle.read(MAX_BYTES+1)
     if len(data)!=attributes.st_size:raise ValueError('file_changed')
    _,after=checked_path(sftp,grant['root'],entry['name'])
    if signature(after)!=entry['signature']:raise ValueError('file_changed')
   return decode_image(data)
  data=await self.run(session,read)
  if not session.alive or session.dashboard.get('photoGrant') is not grant or state.generation!=grant['generation']:raise SourceError('permission_denied')
  return data
