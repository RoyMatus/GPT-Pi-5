"""Open-Meteo model forecast, noncommercial personal prototype, no geolocation."""
import asyncio,json,math,time
from collections import OrderedDict
from datetime import datetime,timezone
import httpx
DEFAULT_LOCATION={'name':'Москва (по умолчанию)','latitude':55.75,'longitude':37.62}

def validate_location(data):
 if not isinstance(data,dict) or set(data)!={'name','latitude','longitude'} or not isinstance(data['name'],str) or not 1<=len(data['name'].strip())<=100:raise ValueError('invalid_location')
 for name,limit in [('latitude',90),('longitude',180)]:
  if type(data[name]) not in [int,float] or not math.isfinite(data[name]) or abs(data[name])>limit:raise ValueError('invalid_location')
 return {'name':data['name'].strip(),'latitude':round(data['latitude'],4),'longitude':round(data['longitude'],4)}

def temperature(value):
 if type(value) not in [int,float] or not math.isfinite(value) or not -100<=value<=100:raise ValueError('invalid_weather')
 return value

def stamp(value):
 parsed=datetime.fromisoformat(value)
 return (parsed.replace(tzinfo=timezone.utc) if parsed.tzinfo is None else parsed.astimezone(timezone.utc)).isoformat()

def parse_weather(data):
 if data['current_units']['temperature_2m']!='°C':raise ValueError('invalid_units')
 current=data['current'];now=stamp(current['time']);code=current['weather_code']
 if type(code)!=int or not 0<=code<=99:raise ValueError('invalid_weather')
 forecast=[]
 for day,value in zip(data['hourly']['time'][:72],data['hourly']['temperature_2m'][:72]):
  if stamp(day)>now:forecast.append({'time':stamp(day),'temperature':temperature(value)})
 return {'temperature':temperature(current['temperature_2m']),'code':code,'forecast':forecast[:3],'forecastTime':now}

class Weather:
 def __init__(self,transport=None):self.transport=transport;self.cache=OrderedDict();self.lock=asyncio.Lock()
 async def fetch(self,url,params):
  async with httpx.AsyncClient(timeout=10,transport=self.transport,follow_redirects=False) as client:
   async with client.stream('GET',url,params=params) as response:
    response.raise_for_status();data=bytearray()
    async for chunk in response.aiter_bytes():
     data.extend(chunk)
     if len(data)>256000:raise ValueError('response_limit')
    return json.loads(data)
 async def get(self,location):
  key=(location['latitude'],location['longitude'])
  async with self.lock:
   cached=self.cache.get(key)
   if cached and time.monotonic()<cached[0]:return {**cached[1],'location':location}
   result={'state':'unavailable','temperature':None,'forecast':[],'location':location,'provider':'Open-Meteo'}
   try:
    data=await self.fetch('https://api.open-meteo.com/v1/forecast',{'latitude':key[0],'longitude':key[1],'current':'temperature_2m,weather_code','hourly':'temperature_2m','forecast_days':2,'timezone':'UTC'})
    result.update(**parse_weather(data),state='ready',updatedAt=datetime.now(timezone.utc).isoformat())
    if (datetime.now(timezone.utc)-datetime.fromisoformat(result['forecastTime'])).total_seconds()>7200:result['state']='stale'
    ttl=600
   except (httpx.HTTPError,ValueError,KeyError,TypeError,IndexError):
    if cached and cached[1].get('temperature') is not None:result={**cached[1],'state':'stale'}
    ttl=30
   self.cache[key]=(time.monotonic()+ttl,result);self.cache.move_to_end(key)
   while len(self.cache)>64:self.cache.popitem(last=False)
   return {**result,'location':location}
 async def search(self,query):
  if not isinstance(query,str) or not 2<=len(query.strip())<=80:raise ValueError('invalid_location')
  data=await self.fetch('https://geocoding-api.open-meteo.com/v1/search',{'name':query.strip(),'count':5,'language':'ru','format':'json'})
  result=[]
  for item in data.get('results',[])[:5]:
   result.append(validate_location({'name':', '.join(str(item.get(k,''))[:60] for k in ['name','admin1','country'] if item.get(k))[:100],'latitude':item['latitude'],'longitude':item['longitude']}))
  return result
