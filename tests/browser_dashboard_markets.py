"""Synthetic market watchlist/period UI; live providers are intercepted."""
import os,socket,tempfile
from pathlib import Path
from urllib.parse import urlparse,parse_qs
from playwright.sync_api import sync_playwright
from browser_remember_login import Server
from gpt_pi.config import Settings

def check():
 with tempfile.TemporaryDirectory() as directory,sync_playwright() as p:
  with socket.socket() as listener:listener.bind(('127.0.0.1',0));port=listener.getsockname()[1]
  settings=Settings(port=port,data_dir=Path(directory));server=Server(settings);server.start()
  browser=p.chromium.launch(channel=os.environ.get('GPT_PI_TEST_BROWSER_CHANNEL'))
  try:
   page=browser.new_page(viewport={'width':720,'height':1280});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
   catalog=[{'id':'kraken:XBTUSD','label':'BTC / USD','category':'crypto','currency':'USD','provider':'Synthetic'},{'id':'kraken:ETHUSD','label':'ETH / USD','category':'crypto','currency':'USD','provider':'Synthetic'}];watch=[x['id'] for x in catalog]
   def quote(identifier,period):
    row=next(x for x in catalog if x['id']==identifier);return {**row,'period':period,'value':110,'change':10,'history':[{'time':'2026-11-10','value':100},{'time':'2026-11-11','value':110}],'state':'ready','quoteTime':'2026-11-11','detail':'Synthetic only'}
   def market(route):
    if route.request.method=='POST':watch[:]=route.request.post_data_json['watchlist']
    query=parse_qs(urlparse(route.request.url).query);selected=query.get('instrument',['kraken:XBTUSD'])[0];period=query.get('period',['1D'])[0]
    route.fulfill(json={'catalog':catalog,'watchlist':watch,'quotes':[quote(i,'1D') for i in watch],'selected':quote(selected,period)})
   page.route('**/api/dashboard/markets*',market);page.goto(settings.origin+'/?dashboard');page.get_by_role('button',name='Рынки',exact=True).click()
   page.get_by_role('button',name='1W',exact=True).click();page.get_by_role('img',name='BTC / USD: 1W',exact=True).wait_for()
   page.get_by_role('button',name='Убрать BTC / USD',exact=True).click();page.get_by_role('button',name='Убрать BTC / USD',exact=True).wait_for(state='detached')
   page.get_by_label('Добавить инструмент',exact=True).select_option('kraken:XBTUSD');page.get_by_role('button',name='Добавить',exact=True).click();page.get_by_role('button',name='Убрать BTC / USD',exact=True).wait_for()
   page.get_by_role('button',name='Выше',exact=True).nth(1).click()
   page.wait_for_timeout(100);assert watch[0]=='kraken:XBTUSD';assert not errors,errors
   print('PASS: synthetic markets selection, periods, remove/add/reorder')
  finally:browser.close();server.stop()
if __name__=='__main__':check()
