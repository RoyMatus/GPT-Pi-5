"""Synthetic Overview agreement, anonymous boot and weather locality selection."""
import os,socket,tempfile
from pathlib import Path
from playwright.sync_api import sync_playwright
from browser_remember_login import Server
from gpt_pi.config import Settings

def check():
 with tempfile.TemporaryDirectory() as directory,sync_playwright() as p:
  with socket.socket() as listener:listener.bind(('127.0.0.1',0));port=listener.getsockname()[1]
  settings=Settings(port=port,data_dir=Path(directory));server=Server(settings);server.start();browser=p.chromium.launch(channel=os.environ.get('GPT_PI_TEST_BROWSER_CHANNEL'))
  try:
   page=browser.new_page(viewport={'width':720,'height':1280});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
   weather={'state':'ready','temperature':0,'code':3,'forecast':[],'forecastTime':'2026-11-11T10:00:00Z','location':{'name':'Synthetic city','latitude':1,'longitude':2}}
   def forecast(route):
    if route.request.method=='POST':weather['location']=route.request.post_data_json
    route.fulfill(json=weather)
   page.route('**/api/dashboard/weather',forecast);page.route('**/api/dashboard/weather/search*',lambda r:r.fulfill(json={'locations':[{'name':'Selected synthetic city','latitude':3,'longitude':4}]}))
   page.route('**/api/dashboard/computer',lambda r:r.fulfill(json={'state':'ready','profile':None,'sample':{'source':'Synthetic PC','values':{'cpuPct':72},'acquiredAt':'2026-11-11T10:00:00Z'},'history':[]}))
   q={'id':'kraken:XBTUSD','label':'BTC / USD','category':'crypto','currency':'USD','provider':'Synthetic','state':'ready','value':110,'change':10,'history':[{'value':100},{'value':110}],'period':'1D'}
   page.route('**/api/dashboard/markets*',lambda r:r.fulfill(json={'quotes':[q],'selected':q,'catalog':[q],'watchlist':[q['id']]}))
   page.goto(settings.origin+'/?dashboard');page.get_by_text('72%',exact=True).wait_for();assert len(server.app.state.runtime.sessions)==1
   page.get_by_role('button',name='Подробнее',exact=True).click();page.get_by_text('72%',exact=True).wait_for();page.get_by_role('button',name='Обзор',exact=True).click();page.get_by_role('link',name='Открыть BTC / USD',exact=True).click();page.get_by_role('button',name='1W',exact=True).wait_for()
   page.get_by_role('button',name='Обзор',exact=True).click();page.get_by_role('button',name='Выбрать город',exact=True).click();page.get_by_label('Название города',exact=True).fill('Synthetic');page.get_by_role('button',name='Найти город',exact=True).click();page.get_by_role('button',name='Selected synthetic city',exact=True).click();page.get_by_text('Selected synthetic city',exact=True).wait_for();assert not errors,errors
   print('PASS: one anonymous session, shared summary/detail values, weather selection')
  finally:browser.close();server.stop()
if __name__=='__main__':check()
