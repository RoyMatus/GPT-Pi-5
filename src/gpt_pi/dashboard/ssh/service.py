"""Verified SSH/SFTP backend. Never accepts arbitrary executable commands."""
import asyncio,base64,hashlib,io,json,math,os,re,secrets,shlex,socket,time
from contextlib import contextmanager
from datetime import datetime,timezone
from pathlib import Path
import paramiko
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization

FIELDS=('cpuPct','cpuGHz','cpuTemp','gpuPct','gpuTemp','gpuMemoryUsed','gpuMemoryTotal','gpuWatts','ramUsed','ramTotal','diskUsed','diskTotal','netRxBytes','netTxBytes','netRxBitsPerSecond','netTxBitsPerSecond','uptime','fanRpm')

def windows_collector_script():
 collectors=Path(__file__).parent/'collectors'
 return collectors.joinpath('windows.ps1').read_text(encoding='utf-8').replace(
  '# GPT_PI_OPTIONAL_SENSOR_FUNCTIONS',collectors.joinpath('windows-sensors.ps1').read_text(encoding='utf-8'),1)

class SourceError(Exception):
 def __init__(self,code):self.code=code;super().__init__(code)

def fingerprint(key):return 'SHA256:'+base64.b64encode(hashlib.sha256(key.asbytes()).digest()).decode().rstrip('=')
class PinnedHost(paramiko.MissingHostKeyPolicy):
 def __init__(self,expected):self.expected=expected
 def missing_host_key(self,client,hostname,key):
  if not self.expected:raise SourceError('verification_required')
  if not secrets.compare_digest(fingerprint(key),self.expected):raise SourceError('host_key_changed')

def validate_profile(data):
 allowed={'host','port','user','platform','fingerprint','photoUser','label','verified'}
 if not isinstance(data,dict) or set(data)-allowed or data.get('verified') is not True:raise ValueError('invalid_profile')
 host=data.get('host','');port=data.get('port',22);user=data.get('user','');photo=data.get('photoUser') or user
 if not isinstance(host,str) or not re.fullmatch(r'[A-Za-z0-9.:%_-]{1,253}',host):raise ValueError('invalid_profile')
 if type(port)!=int or not 1<=port<=65535:raise ValueError('invalid_profile')
 if any(not isinstance(u,str) or not 1<=len(u)<=128 or any(ord(c)<32 for c in u) for u in [user,photo]):raise ValueError('invalid_profile')
 if data.get('platform') not in ['linux','windows']:raise ValueError('invalid_profile')
 if not re.fullmatch(r'SHA256:[A-Za-z0-9+/]{43}',data.get('fingerprint','')):raise ValueError('verification_required')
 label=data.get('label','Мой компьютер')
 if not isinstance(label,str) or not 1<=len(label.strip())<=48:raise ValueError('invalid_profile')
 return {'host':host,'port':port,'user':user,'photoUser':photo,'platform':data['platform'],'fingerprint':data['fingerprint'],'label':label.strip(),'enabled':True}

def validate_sample(data):
 if not isinstance(data,dict) or type(data.get('schema'))!=int or data.get('schema')!=1 or set(data)-set(FIELDS)-{'schema'}:raise ValueError('invalid_sample')
 result={}
 for key in FIELDS:
  value=data.get(key)
  if value is not None and (type(value) not in [int,float] or not math.isfinite(value) or value<0 or (key.endswith('Pct') and value>100) or value>10**18):raise ValueError('invalid_sample')
  if value is not None:
   if key.endswith('Temp') and value>200:raise ValueError('invalid_sample')
   if key=='cpuGHz' and value>20:raise ValueError('invalid_sample')
   if key=='fanRpm' and value>100000:raise ValueError('invalid_sample')
  result[key]=value
 for used,total in [('ramUsed','ramTotal'),('diskUsed','diskTotal'),('gpuMemoryUsed','gpuMemoryTotal')]:
  if result[used] is not None and result[total] is not None and result[used]>result[total]:raise ValueError('invalid_sample')
 if not result.get('ramTotal') or not result.get('diskTotal'):raise ValueError('invalid_sample')
 return result

def network_rates(previous,current):
 if not previous or any(current.get(k) is None or previous.get(k) is None for k in ['netRxBytes','netTxBytes','uptime']):return None,None
 elapsed=current['uptime']-previous['uptime'];rx=current['netRxBytes']-previous['netRxBytes'];tx=current['netTxBytes']-previous['netTxBytes']
 if elapsed<=0 or rx<0 or tx<0:return None,None
 return rx*8/elapsed,tx*8/elapsed

def write_private(path,data):
 path.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
 temporary=path.with_suffix('.tmp');fd=os.open(temporary,os.O_WRONLY|os.O_CREAT|os.O_TRUNC,0o600)
 with os.fdopen(fd,'w',encoding='utf-8') as output:output.write(data)
 os.replace(temporary,path)

def key_pair(path):
 if not path.exists():
  key=Ed25519PrivateKey.generate()
  write_private(path,key.private_bytes(serialization.Encoding.PEM,serialization.PrivateFormat.OpenSSH,serialization.NoEncryption()).decode())
 return paramiko.Ed25519Key.from_private_key(io.StringIO(path.read_text(encoding='utf-8')))

class ComputerState:
 def __init__(self,path):
  self.path=path;self.profile=None;self.generation=0;self.previous=None;self.sample=None;self.history=[];self.updated=0;self.lock=asyncio.Lock();self.clients=set()
  if (path/'profile.json').exists():
   raw=json.loads((path/'profile.json').read_text(encoding='utf-8'))
   enabled=raw.pop('enabled',False);self.profile=validate_profile({**raw,'verified':True});self.profile['enabled']=bool(enabled)
 def reset(self):
  self.generation+=1;self.previous=None;self.sample=None;self.history=[];self.updated=0
  for client in list(self.clients):client.close()
 def public(self):
  result={'profile':self.profile,'generation':self.generation,'state':'not_configured' if not self.profile else 'disabled' if not self.profile['enabled'] else 'configured','sample':self.sample,'history':self.history[-60:]}
  if self.profile:
   result['publicKey']=key_pair(self.path/'telemetry.key').get_name()+' '+key_pair(self.path/'telemetry.key').get_base64()
   result['photoPublicKey']=key_pair(self.path/'photos.key').get_name()+' '+key_pair(self.path/'photos.key').get_base64()
  return result
 def configure(self,data):
  profile=validate_profile(data);self.reset();self.profile=profile
  key_pair(self.path/'telemetry.key');key_pair(self.path/'photos.key');write_private(self.path/'profile.json',json.dumps(profile))
 def disable(self,remove=False):
  self.reset()
  if self.profile:self.profile['enabled']=False;write_private(self.path/'profile.json',json.dumps(self.profile))
  if remove:
   for name in ['telemetry.key','photos.key','profile.json']:(self.path/name).unlink(missing_ok=True)
   self.profile=None
 @contextmanager
 def connect(self,session,photo=False):
  profile=self.profile
  if not session.alive:raise SourceError('session_expired')
  if not profile or not profile['enabled']:raise SourceError('not_configured')
  mark=self.generation;client=paramiko.SSHClient();client.set_missing_host_key_policy(PinnedHost(profile['fingerprint']))
  self.clients.add(client);session.resources.add(client)
  try:
   if not session.alive or mark!=self.generation:raise SourceError('session_expired')
   key=key_pair(self.path/('photos.key' if photo else 'telemetry.key'))
   client.connect(profile['host'],port=profile['port'],username=profile['photoUser'] if photo else profile['user'],pkey=key,look_for_keys=False,allow_agent=False,timeout=5,auth_timeout=5,banner_timeout=5,channel_timeout=8)
   if not session.alive or mark!=self.generation:raise SourceError('session_expired')
   yield client
  except paramiko.AuthenticationException:raise SourceError('authentication_failed') from None
  except paramiko.BadHostKeyException:raise SourceError('host_key_changed') from None
  except (socket.timeout,TimeoutError):raise SourceError('timeout') from None
  except (OSError,paramiko.SSHException):raise SourceError('unreachable') from None
  finally:client.close();self.clients.discard(client);session.resources.discard(client)
 @contextmanager
 def sftp(self,session,grant):
  # Grant identity is held by the live session, never a supplied owner/root ID.
  if not isinstance(grant,dict) or not session.alive or session.dashboard.get('photoGrant') is not grant or grant.get('generation')!=self.generation:raise SourceError('permission_denied')
  with self.connect(session,photo=True) as client:
   sftp=client.open_sftp();sftp.get_channel().settimeout(8)
   try:yield sftp
   finally:sftp.close()
 def collect_sync(self,session):
  platform=self.profile['platform'] if self.profile else None
  with self.connect(session) as client:
   if platform=='linux':command='python3 -c '+shlex.quote((Path(__file__).parent/'collectors/linux.py').read_text(encoding='utf-8'))
   else:
    encoded=base64.b64encode(windows_collector_script().encode('utf-16le')).decode()
    command='powershell.exe -NoLogo -NoProfile -NonInteractive -EncodedCommand '+encoded
   channel=client.get_transport().open_session(timeout=5);channel.settimeout(8);channel.exec_command(command)
   deadline=time.monotonic()+12;output=bytearray();errors=0
   try:
    while True:
     if not session.alive:raise SourceError('session_expired')
     if time.monotonic()>deadline:raise SourceError('timeout')
     while channel.recv_ready():
      output.extend(channel.recv(8192))
      if len(output)>65536:raise SourceError('invalid_sample')
     while channel.recv_stderr_ready():
      errors+=len(channel.recv_stderr(8192))
      if errors>65536:raise SourceError('collector_failed')
     if channel.exit_status_ready() and not channel.recv_ready():break
     time.sleep(.02)
    if channel.recv_exit_status()!=0:raise SourceError('collector_failed')
    try:return validate_sample(json.loads(output.decode('utf-8-sig')))
    except (ValueError,TypeError,UnicodeError):raise SourceError('invalid_sample') from None
   finally:channel.close()
 async def collect(self,session):
  async with self.lock:
   if not self.profile or not self.profile['enabled']:return self.public()
   if time.monotonic()-self.updated<3:return {**self.public(),'state':self.sample.get('state','configured') if self.sample else 'configured'}
   mark=self.generation;task=asyncio.current_task();session.dashboard_tasks.add(task)
   try:
    sample=await asyncio.wait_for(asyncio.to_thread(self.collect_sync,session),20)
    if not session.alive or mark!=self.generation:raise SourceError('session_expired')
    rx,tx=network_rates(self.previous,sample);self.previous=sample
    if sample['netRxBitsPerSecond'] is None:sample['netRxBitsPerSecond']=rx
    if sample['netTxBitsPerSecond'] is None:sample['netTxBitsPerSecond']=tx
    self.sample={'state':'ready','values':sample,'supported':{k:v is not None for k,v in sample.items()},'acquiredAt':datetime.now(timezone.utc).isoformat(),'generation':mark,'source':self.profile['label']}
    self.history.append({'cpuPct':sample['cpuPct'],'gpuPct':sample['gpuPct'],'netRxBitsPerSecond':sample['netRxBitsPerSecond']});self.history=self.history[-60:]
   except (SourceError,TimeoutError) as exc:
    code=exc.code if isinstance(exc,SourceError) else 'timeout'
    if isinstance(exc,TimeoutError):
     for client in list(session.resources):client.close()
    if mark==self.generation:self.sample={**(self.sample or {}),'state':code,'stale':bool(self.sample)}
   except asyncio.CancelledError:
    for client in list(session.resources):client.close()
    raise
   finally:session.dashboard_tasks.discard(task);self.updated=time.monotonic()
   result=self.public()
   if result['state']=='configured' and self.sample:result['state']=self.sample['state']
   return result

class ComputerService:
 def __init__(self,data_dir):self.path=Path(data_dir)/'dashboard/ssh';self.states={}
 def state(self,session):
  if not session.alive or not session.connection:raise SourceError('session_expired')
  owner=hashlib.sha256(session.connection.subject.encode()).hexdigest()
  if owner not in self.states:self.states[owner]=ComputerState(self.path/owner)
  return self.states[owner]
