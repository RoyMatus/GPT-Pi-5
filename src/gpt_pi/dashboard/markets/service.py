"""Bounded public read-only market adapters; fixed provider URLs, no API keys."""
import asyncio
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import math
import time
from xml.etree import ElementTree
import httpx

CATALOG={
 'kraken:XBTUSD':{'label':'BTC / USD','category':'crypto','currency':'USD','provider':'Kraken','symbol':'XBTUSD'},
 'kraken:ETHUSD':{'label':'ETH / USD','category':'crypto','currency':'USD','provider':'Kraken','symbol':'ETHUSD'},
 'moex:TQBR:SBER':{'label':'SBER · MOEX','category':'stock','currency':'RUB','provider':'MOEX ISS','symbol':'SBER','market':'shares','board':'TQBR'},
 'moex:SNDX:IMOEX':{'label':'IMOEX · MOEX','category':'index','currency':'points','provider':'MOEX ISS','symbol':'IMOEX','market':'index','board':'SNDX'},
 'cbr:USD:RUB':{'label':'USD / RUB','category':'fx','currency':'RUB','provider':'Банк России','symbol':'USD'},
 'cbr:EUR:RUB':{'label':'EUR / RUB','category':'fx','currency':'RUB','provider':'Банк России','symbol':'EUR'},
 'unsupported:oil':{'label':'Нефть','category':'commodity','currency':'USD','provider':'Не подключён','symbol':'Oil'},
 'unsupported:gold':{'label':'Золото','category':'commodity','currency':'USD','provider':'Не подключён','symbol':'Gold'},
}
PERIODS={'1D':(1,60),'1W':(7,60),'1M':(30,1440),'1Y':(365,1440)}

def number(value):
 if isinstance(value,bool):raise ValueError('invalid_number')
 result=float(value)
 if not math.isfinite(result) or result<0:raise ValueError('invalid_number')
 return result

def change_percent(value,baseline):
 if value is None or baseline is None or baseline==0:return None
 return float((Decimal(str(value))-Decimal(str(baseline)))/Decimal(str(baseline))*100)

def parse_cbr(data,symbol):
 if len(data)>512000 or b'<!DOCTYPE' in data.upper() or b'<!ENTITY' in data.upper():raise ValueError('invalid_xml')
 root=ElementTree.fromstring(data)
 for item in root.findall('Valute'):
  if item.findtext('CharCode')==symbol:
   value=Decimal(item.findtext('Value','').replace(',','.'))/Decimal(item.findtext('Nominal','0'))
   return number(value),datetime.strptime(root.attrib['Date'],'%d.%m.%Y').date().isoformat()
 raise ValueError('unsupported_symbol')

def parse_kraken(data):
 if data.get('error'):raise ValueError('provider_error')
 rows=next((v for k,v in data['result'].items() if k!='last'),[])
 if not rows or len(rows)>1024:raise ValueError('empty_series')
 result=[]
 for row in rows:
  if not isinstance(row,list) or len(row)!=8:raise ValueError('invalid_series')
  stamp=datetime.fromtimestamp(number(row[0]),timezone.utc).isoformat()
  result.append({'time':stamp,'value':number(row[4])})
 if any(a['time']>=b['time'] for a,b in zip(result,result[1:])):raise ValueError('unordered_series')
 return result

class Markets:
 def __init__(self,transport=None):
  self.transport=transport;self.cache={};self.locks={};self.semaphore=asyncio.Semaphore(3)
 async def fetch(self,url,params=None):
  async with self.semaphore, httpx.AsyncClient(timeout=10,transport=self.transport,follow_redirects=False) as client:
   async with client.stream('GET',url,params=params) as response:
    response.raise_for_status();data=bytearray()
    async for chunk in response.aiter_bytes():
     data.extend(chunk)
     if len(data)>512000:raise ValueError('response_limit')
    return bytes(data)
 async def quote(self,identifier,period='1D'):
  if identifier not in CATALOG or period not in PERIODS:raise ValueError('invalid_instrument')
  key=(identifier,period)
  async with self.locks.setdefault(key,asyncio.Lock()):
   cached=self.cache.get(key)
   if cached and time.monotonic()<cached[0]:return cached[1]
   instrument=CATALOG[identifier];days,interval=PERIODS[period]
   base={'id':identifier,**instrument,'period':period,'value':None,'change':None,'history':[],'state':'unavailable','quoteTime':None,'updatedAt':datetime.now(timezone.utc).isoformat()}
   if identifier.startswith('unsupported:'):
    return {**base,'state':'unsupported','detail':'Поставщик и конкретный spot/futures контракт не подключены'}
   try:
    import json
    if instrument['provider']=='Kraken':
     raw=await self.fetch('https://api.kraken.com/0/public/OHLC',{'pair':instrument['symbol'],'interval':interval})
     history=parse_kraken(json.loads(raw))[-(days*24 if interval==60 else days):]
     detail='Свечи Kraken · изменение за выбранный период · круглосуточно'
    elif instrument['provider']=='Банк России':
     raw=await self.fetch('https://www.cbr.ru/scripts/XML_daily.asp')
     price,day=parse_cbr(raw,instrument['symbol'])
     code={'USD':'R01235','EUR':'R01239'}[instrument['symbol']]
     start=(datetime.now()-timedelta(days=days)).strftime('%d/%m/%Y')
     raw=await self.fetch('https://www.cbr.ru/scripts/XML_dynamic.asp',{'date_req1':start,'date_req2':datetime.now().strftime('%d/%m/%Y'),'VAL_NM_RQ':code})
     if b'<!DOCTYPE' in raw.upper() or b'<!ENTITY' in raw.upper():raise ValueError('invalid_xml')
     root=ElementTree.fromstring(raw);history=[]
     for record in root.findall('Record'):
      history.append({'time':datetime.strptime(record.attrib['Date'],'%d.%m.%Y').date().isoformat(),'value':number(Decimal(record.findtext('Value','').replace(',','.'))/Decimal(record.findtext('Nominal','0')))})
     if not history or history[-1]['time']!=day:history.append({'time':day,'value':price})
     detail='Официальный курс ЦБ за 1 единицу · не биржевая котировка'
    else:
     url=f"https://iss.moex.com/iss/engines/stock/markets/{instrument['market']}/boards/{instrument['board']}/securities/{instrument['symbol']}/candles.json"
     raw=await self.fetch(url,{'iss.meta':'off','from':(datetime.now()-timedelta(days=days+7)).date().isoformat(),'interval':60 if interval==60 else 24})
     block=json.loads(raw)['candles'];columns=block['columns'];history=[]
     for row in block['data'][:500]:
      item=dict(zip(columns,row));stamp=datetime.fromisoformat(item['begin']).replace(tzinfo=timezone(timedelta(hours=3)))
      history.append({'time':stamp.isoformat(),'value':number(item['close'])})
     if period=='1D' and history:
      last_day=history[-1]['time'][:10];history=[point for point in history if point['time'].startswith(last_day)]
     detail='MOEX ISS · задержанные свечи · последняя доступная сессия'
    if not history:raise ValueError('empty_series')
    base.update(value=history[-1]['value'],change=change_percent(history[-1]['value'],history[0]['value'] if len(history)>1 else None),history=history,quoteTime=history[-1]['time'],state='ready',detail=detail)
    # A quote timestamp is distinct from successful acquisition. Old series stay visibly stale.
    quote_day=base['quoteTime'][:10]
    if quote_day<(datetime.now(timezone.utc)-timedelta(days=4)).date().isoformat():base['state']='stale'
    self.cache[key]=(time.monotonic()+60,base)
   except (httpx.HTTPError,ValueError,KeyError,TypeError,IndexError,ArithmeticError,ElementTree.ParseError) as exc:
    base={**(cached[1] if cached and cached[1]['value'] is not None else base),'state':'stale' if cached and cached[1]['value'] is not None else 'unavailable','detail':'Источник временно недоступен; повтор не чаще 30 секунд'}
    base['errorCode']='rate_limited' if isinstance(exc,httpx.HTTPStatusError) and exc.response.status_code==429 else 'provider_unavailable'
    if base['errorCode']=='rate_limited':base['detail']='Лимит источника; повтор не раньше 30 секунд'
    self.cache[key]=(time.monotonic()+30,base)
   return base
 async def snapshot(self,watchlist,selected,period):
  rows=await asyncio.gather(*(self.quote(i,'1D') for i in watchlist))
  return {'catalog':[{'id':k,**v} for k,v in CATALOG.items()],'quotes':rows,'selected':await self.quote(selected,period),'watchlist':watchlist}
