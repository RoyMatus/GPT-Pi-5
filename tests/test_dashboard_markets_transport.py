import asyncio,json,unittest
import httpx
from gpt_pi.dashboard.markets.service import Markets
class MarketTransportTests(unittest.IsolatedAsyncioTestCase):
 async def test_single_refresh_shared_snapshot_and_stale_backoff(self):
  calls=[];fail=[False]
  def reply(request):
   calls.append(request.url.path)
   if fail[0]:return httpx.Response(429)
   return httpx.Response(200,json={'error':[],'result':{'XXBTZUSD':[[1794300000,'100','110','90','100','100','1',1],[1794303600,'100','120','100','110','110','1',1]],'last':1794303600}})
  service=Markets(httpx.MockTransport(reply))
  a,b=await asyncio.gather(service.quote('kraken:XBTUSD'),service.quote('kraken:XBTUSD'))
  self.assertEqual(len(calls),1);self.assertEqual(a['value'],110);self.assertEqual(a['change'],10)
  snapshot=await service.snapshot(['kraken:XBTUSD'],'kraken:XBTUSD','1D')
  self.assertEqual(snapshot['quotes'][0]['value'],snapshot['selected']['value']);self.assertEqual(len(calls),1)
  service.cache[('kraken:XBTUSD','1D')]=(0,a);fail[0]=True
  stale=await service.quote('kraken:XBTUSD');self.assertEqual(stale['state'],'stale');self.assertEqual(stale['value'],110)
  await service.quote('kraken:XBTUSD');self.assertEqual(len(calls),2)
 async def test_unsupported_commodity_never_substitutes_a_price(self):
  service=Markets(httpx.MockTransport(lambda request: (_ for _ in ()).throw(AssertionError('Network forbidden'))))
  result=await service.quote('unsupported:oil');self.assertEqual(result['state'],'unsupported');self.assertIsNone(result['value'])
