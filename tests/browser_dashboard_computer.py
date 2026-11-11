"""Synthetic Computer setup/trust-state UI, without a network SSH target."""
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
   page=browser.new_page(viewport={'width':720,'height':1280});state={'profile':None,'state':'not_configured','sample':None,'history':[]};errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
   def computer(route):
    if route.request.method=='POST':
     data=route.request.post_data_json
     if data['action']=='configure':state.update(profile={k:v for k,v in data.items() if k not in ['action','verified']},state='configured',publicKey='ssh-ed25519 synthetic-telemetry',photoPublicKey='ssh-ed25519 synthetic-photo')
     elif data['action']=='disable':state['state']='disabled'
    route.fulfill(json=state)
   page.route('**/api/dashboard/computer',computer);page.goto(settings.origin+'/?dashboard');page.get_by_role('button',name='Компьютер',exact=True).click();page.get_by_role('button',name='Настроить компьютер').click()
   page.get_by_label('Адрес SSH',exact=True).fill('synthetic.invalid');page.get_by_label('Пользователь телеметрии',exact=True).fill('metrics');page.get_by_label('Проверенный SHA256-отпечаток SSH-сервера',exact=True).fill('SHA256:'+'a'*43)
   save=page.get_by_role('button',name='Сохранить подключение');assert not save.is_enabled();page.get_by_label('Я сверил отпечаток по доверенному каналу').check();save.click();page.get_by_label('Публичный ключ телеметрии',exact=True).wait_for();assert state['profile']['host']=='synthetic.invalid'
   state['state']='host_key_changed';page.get_by_role('button',name='Обновить',exact=True).click();page.get_by_text('Ключ сервера изменился — подключение заблокировано',exact=False).first.wait_for()
   page.get_by_role('button',name='Отключить',exact=True).click();page.get_by_text('Подключение отключено',exact=False).first.wait_for();assert 'PRIVATE KEY' not in page.content();assert not errors,errors
   print('PASS: synthetic SSH setup, explicit trust confirmation, key-change and disable states')
  finally:browser.close();server.stop()
if __name__=='__main__':check()
