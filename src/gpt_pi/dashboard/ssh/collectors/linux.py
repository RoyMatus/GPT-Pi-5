"""Fixed Linux collector. Runs once under SSH; no installation/background daemon."""
import glob,json,os,shutil,subprocess,time
from pathlib import Path

def cpu():
 values=[int(x) for x in Path('/proc/stat').read_text().splitlines()[0].split()[1:9]]
 return sum(values),values[3]+(values[4] if len(values)>4 else 0)
def net():
 rows=Path('/proc/net/dev').read_text().splitlines()[2:];rx=tx=0
 for row in rows:
  name,values=row.split(':',1)
  if name.strip()=='lo':continue
  fields=values.split();rx+=int(fields[0]);tx+=int(fields[8])
 return rx,tx
first=cpu();time.sleep(.25);last=cpu();total=last[0]-first[0]
mem={k:int(v.split()[0])*1024 for k,v in (line.split(':',1) for line in Path('/proc/meminfo').read_text().splitlines()) if v.strip().split()[0].isdigit()}
disk=shutil.disk_usage('/');rx,tx=net()
data=dict(schema=1,cpuPct=100*(1-(last[1]-first[1])/total) if total else None,cpuGHz=None,cpuTemp=None,gpuPct=None,gpuTemp=None,gpuMemoryUsed=None,gpuMemoryTotal=None,gpuWatts=None,ramUsed=mem['MemTotal']-mem.get('MemAvailable',mem['MemFree']),ramTotal=mem['MemTotal'],diskUsed=disk.used,diskTotal=disk.total,netRxBytes=rx,netTxBytes=tx,netRxBitsPerSecond=None,netTxBitsPerSecond=None,uptime=float(Path('/proc/uptime').read_text().split()[0]),fanRpm=None)
for name in glob.glob('/sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq'):
 try:data['cpuGHz']=float(Path(name).read_text())/1000000
 except (OSError,ValueError):pass
for name in glob.glob('/sys/class/thermal/thermal_zone*')[:32]:
 try:
  kind=Path(name+'/type').read_text().lower()
  if any(word in kind for word in ['cpu','soc','x86']):data['cpuTemp']=float(Path(name+'/temp').read_text())/1000;break
 except (OSError,ValueError):pass
for name in glob.glob('/sys/class/hwmon/hwmon*/fan1_input')[:16]:
 try:data['fanRpm']=float(Path(name).read_text());break
 except (OSError,ValueError):pass
if shutil.which('nvidia-smi'):
 try:
  r=subprocess.run(['nvidia-smi','--query-gpu=utilization.gpu,temperature.gpu,memory.used,memory.total,power.draw','--format=csv,noheader,nounits'],capture_output=True,text=True,timeout=2)
  if r.returncode==0:
   values=r.stdout.splitlines()[0].split(',');data.update(gpuPct=float(values[0]),gpuTemp=float(values[1]),gpuMemoryUsed=float(values[2])*1048576,gpuMemoryTotal=float(values[3])*1048576,gpuWatts=float(values[4]))
 except (OSError,ValueError,subprocess.TimeoutExpired,IndexError):pass
print(json.dumps(data,allow_nan=False))
