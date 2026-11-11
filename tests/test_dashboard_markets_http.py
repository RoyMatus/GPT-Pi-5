import unittest,time
import httpx
import test_webapp as harness
class MarketHTTPTests(unittest.TestCase):
 setUp=harness.WebTests.setUp
 tearDown=harness.WebTests.tearDown
 post=harness.WebTests.post
 def test_catalog_only_and_watchlist_isolation_without_real_providers(self):
  def reply(request):
   if 'kraken' in request.url.host:return httpx.Response(200,json={'error':[],'result':{'PAIR':[[int(time.time())-3600,'1','2','0','10','1','1',1],[int(time.time()),'1','2','0','11','1','1',1]]}})
   if 'XML_daily' in request.url.path:return httpx.Response(200,content=b'<ValCurs Date="10.11.2026"><Valute><CharCode>USD</CharCode><Nominal>1</Nominal><Value>90,0</Value></Valute><Valute><CharCode>EUR</CharCode><Nominal>1</Nominal><Value>100,0</Value></Valute></ValCurs>')
   if 'XML_dynamic' in request.url.path:return httpx.Response(200,content=b'<ValCurs/>')
   return httpx.Response(200,json={'candles':{'columns':['close','begin'],'data':[[100,'2026-11-10 12:00:00']]}})
  self.app.state.runtime.markets.transport=httpx.MockTransport(reply)
  result=self.client.get('/api/dashboard/markets').json();self.assertEqual(result['selected']['value'],11)
  self.assertEqual(self.client.get('/api/dashboard/markets?instrument=https://evil.invalid').status_code,400)
  self.assertEqual(self.post('/api/dashboard/markets',{'watchlist':['kraken:XBTUSD','kraken:XBTUSD']}).status_code,400)
  self.assertEqual(self.post('/api/dashboard/markets',{'watchlist':[]}).json()['watchlist'],[])
  other=harness.TestClient(self.app,base_url=self.settings.origin);other.get('/api/session')
  self.assertEqual(len(other.get('/api/dashboard/markets').json()['watchlist']),6);other.close()
