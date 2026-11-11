"""Synthetic fullscreen slideshow, controls, Escape and object-URL cleanup."""
import io,os,socket,tempfile
from pathlib import Path
from PIL import Image
from playwright.sync_api import sync_playwright
from browser_remember_login import Server
from gpt_pi.config import Settings

def wait_urls_closed(page):
 for _ in range(60):
  if page.evaluate('photoUrls.size')==0:return
  page.wait_for_timeout(50)
 raise AssertionError('Photo object URLs remain live')

def check():
 with tempfile.TemporaryDirectory() as directory,sync_playwright() as p:
  with socket.socket() as listener:listener.bind(('127.0.0.1',0));port=listener.getsockname()[1]
  settings=Settings(port=port,data_dir=Path(directory));server=Server(settings);server.start();browser=p.chromium.launch(channel=os.environ.get('GPT_PI_TEST_BROWSER_CHANNEL'))
  try:
   page=browser.new_page(viewport={'width':720,'height':1280});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
   photo_requests=[];page.on('request',lambda request:photo_requests.append(request.url) if '/api/dashboard/photos/' in request.url else None)
   page.add_init_script('''window.photoUrls=new Set();const create=URL.createObjectURL.bind(URL),revoke=URL.revokeObjectURL.bind(URL);URL.createObjectURL=b=>{const u=create(b);photoUrls.add(u);return u;};URL.revokeObjectURL=u=>{photoUrls.delete(u);revoke(u);};''')
   data=io.BytesIO();Image.new('RGB',(640,480),'#40789a').save(data,'JPEG')
   page.route('**/api/dashboard/photos',lambda r:r.fulfill(json={'state':'ready','files':[{'id':'synthetic-a','name':'a.jpg'},{'id':'synthetic-b','name':'b.jpg'}]}))
   page.route('**/api/dashboard/photos/*',lambda r:r.fulfill(content_type='image/jpeg',body=data.getvalue()))
   page.goto(settings.origin);page.get_by_role('button',name='Фото',exact=True).click();page.get_by_text('Доступно фотографий: 2',exact=True).wait_for()
   page.get_by_text('Показ слайдов',exact=True).click();page.get_by_label('Интервал, секунд',exact=True).fill('10');page.get_by_label('Размер изображения',exact=True).select_option('contain')
   page.get_by_text('Показ слайдов',exact=True).click();assert not photo_requests, 'Photo content loaded before explicit playback'
   page.get_by_role('button',name='Начать слайд-шоу').click()
   page.get_by_alt_text('Фотография из разрешённой папки').wait_for();page.locator('.dashboard-photo img').evaluate('img=>img.decode()');assert page.get_by_role('navigation',name='Разделы приложения').count()==0
   assert page.locator('.dashboard-photo img').evaluate('img=>getComputedStyle(img).objectFit')=='contain'
   for width,height in [(390,844),(1280,800),(720,1280)]:
    page.set_viewport_size({'width':width,'height':height})
    geometry=page.locator('.dashboard-photo').evaluate('el=>{const r=el.getBoundingClientRect();return {x:r.x,y:r.y,width:r.width,height:r.height,viewportWidth:innerWidth,viewportHeight:innerHeight};}')
    assert abs(geometry['x'])<1 and abs(geometry['y'])<1 and abs(geometry['width']-geometry['viewportWidth'])<1 and abs(geometry['height']-geometry['viewportHeight'])<1, f'Fullscreen photo has unintended outer margins: {geometry}'
   page.get_by_role('button',name='Показать управление фотографиями').click();page.get_by_role('button',name='Следующая',exact=True).click();page.get_by_text('2 / 2',exact=True).wait_for();page.keyboard.press('Escape')
   page.get_by_role('button',name='Начать слайд-шоу').wait_for();wait_urls_closed(page)
   page.get_by_role('button',name='Начать слайд-шоу').click();page.get_by_alt_text('Фотография из разрешённой папки').wait_for();page.evaluate("Object.defineProperty(document,'hidden',{configurable:true,get:()=>true});document.dispatchEvent(new Event('visibilitychange'))")
   wait_urls_closed(page);assert not errors,errors
   print('PASS: fullscreen hides chrome; reveal, next, Escape and hidden-page cleanup')
  finally:browser.close();server.stop()
if __name__=='__main__':check()
