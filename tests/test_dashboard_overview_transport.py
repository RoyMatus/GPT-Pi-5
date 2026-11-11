import unittest,httpx
from gpt_pi.dashboard.overview.weather import Weather
class WeatherTransportTests(unittest.IsolatedAsyncioTestCase):
 async def test_shared_location_cache_and_stale_failure(self):
  calls=[];fail=[False]
  def reply(request):
   calls.append(request.url)
   if fail[0]:return httpx.Response(429)
   return httpx.Response(200,json={'current_units':{'temperature_2m':'°C'},'current':{'time':'2026-11-11T10:00','temperature_2m':0,'weather_code':3},'hourly':{'time':['2026-11-11T11:00'],'temperature_2m':[1]}})
  service=Weather(httpx.MockTransport(reply));location={'name':'Synthetic','latitude':1,'longitude':2}
  first=await service.get(location);second=await service.get({**location,'name':'Other label'})
  self.assertEqual(len(calls),1);self.assertEqual(second['temperature'],0)
  service.cache[(1,2)]=(0,first);fail[0]=True
  stale=await service.get(location);self.assertEqual(stale['state'],'stale');self.assertEqual(stale['temperature'],0)
