"""Calendar browser CRUD with synthetic account, RAM events and no cloud calls."""
import os,socket,tempfile
from pathlib import Path
from urllib.parse import parse_qs,urlparse,urlencode
from playwright.sync_api import sync_playwright
from browser_remember_login import Server
from gpt_pi.config import Settings

def check():
 with tempfile.TemporaryDirectory() as directory,sync_playwright() as p:
  with socket.socket() as listener:listener.bind(('127.0.0.1',0));port=listener.getsockname()[1]
  settings=Settings(port=port,data_dir=Path(directory))
  server=Server(settings);server.start()
  browser=p.chromium.launch(channel=os.environ.get('GPT_PI_TEST_BROWSER_CHANNEL'))
  try:
   page=browser.new_page(viewport={'width':720,'height':1280});captured=[];errors=[]
   page.on('pageerror',lambda e:errors.append(str(e)))
   def auth(route):
    captured.append(parse_qs(urlparse(route.request.url).query));route.fulfill(content_type='text/html',body='Synthetic OAuth')
   page.route('https://auth.openai.com/**',auth);page.goto(settings.origin)
   page.get_by_role('button',name='Continue with ChatGPT').click();page.wait_for_url('https://auth.openai.com/**')
   page.goto(settings.origin+'/auth/callback?'+urlencode({'code':'synthetic-calendar','state':captured[0]['state'][0],'client_id':'oaiapp_calendar'}))
   page.get_by_role('button',name='Завершить сеанс',exact=True).wait_for()
   page.get_by_role('button',name='Календарь',exact=True).click()
   page.get_by_text('Изменить дату отсчёта',exact=True).click();page.get_by_label('Дата отсчёта',exact=True).fill('2027-01-02')
   page.get_by_text('До выбранной даты',exact=True).wait_for();page.get_by_text('Изменить дату отсчёта',exact=True).click()
   page.get_by_role('button',name='Добавить событие').click()
   dialog=page.get_by_role('dialog');dialog.get_by_label('Название',exact=True).fill('Synthetic event');dialog.get_by_label('Дата',exact=True).fill('2027-01-02');dialog.get_by_label('Время (необязательно)').fill('09:30');dialog.get_by_role('button',name='Сохранить').click()
   page.get_by_role('button',name='Synthetic event',exact=True).click();page.get_by_role('dialog').get_by_label('Название',exact=True).fill('Updated synthetic event');page.get_by_role('dialog').get_by_role('button',name='Сохранить').click()
   page.get_by_role('button',name='Updated synthetic event',exact=True).click();page.get_by_role('dialog').get_by_role('button',name='Удалить').click()
   page.get_by_text('Нет событий',exact=True).wait_for();assert not errors,errors
   print('PASS: synthetic calendar CRUD and no browser errors')
  finally:browser.close();server.stop()
if __name__=='__main__':check()
