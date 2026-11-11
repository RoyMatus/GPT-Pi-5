"""Offline production-shell geometry checks; no account, API or real device."""
import argparse
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
evidence = ROOT/'build/dashboard-evidence'
evidence.mkdir(parents=True, exist_ok=True)
try:
    with sync_playwright() as p:
        parser = argparse.ArgumentParser()
        parser.add_argument('--browser-channel', default=None)
        args = parser.parse_args()
        browser = p.chromium.launch(channel=args.browser_channel)
        count=0
        for width,height in [(390,844),(720,1280),(1280,800),(1920,1080)]:
            for dpr in (1,2):
                context=browser.new_context(viewport={'width':width,'height':height},device_scale_factor=dpr)
                page=context.new_page()
                def serve(route):
                    from urllib.parse import urlparse
                    path=urlparse(route.request.url).path
                    if path=='/api/session':
                        route.fulfill(json={'authenticated':False,'csrf':'synthetic','provider':'offline','registrations':[]});return
                    if path=='/api/dashboard/computer':
                        route.fulfill(json={'profile':None,'state':'not_configured','sample':None,'history':[]});return
                    if path=='/api/dashboard/markets':
                        route.fulfill(json={'quotes':[],'catalog':[],'watchlist':[],'selected':None});return
                    if path=='/api/dashboard/calendar':
                        route.fulfill(json={'events':[],'storage':'session'});return
                    if path=='/api/dashboard/photos':
                        route.fulfill(json={'files':[],'state':'not_configured'});return
                    if path=='/api/capabilities':
                        route.fulfill(json={'voice':False});return
                    file=ROOT/'src/gpt_pi/web'/('index.html' if path=='/' else path.lstrip('/'))
                    route.fulfill(path=str(file))
                page.route('http://127.0.0.1:*/**',serve)
                errors=[]
                page.on('pageerror',lambda error:errors.append(str(error)))
                page.goto(f'http://127.0.0.1:{8874}/?dashboard')
                for light in (True,False):
                    if light is False:
                        page.get_by_role('button',name='Обзор',exact=True).click()
                        page.get_by_role('button',name='Настройки',exact=True).click()
                        page.get_by_role('switch').uncheck()
                        page.get_by_role('button',name='Настройки',exact=True).click()
                    for text in (100,200):
                        page.evaluate('(size)=>document.documentElement.style.fontSize=size+"%"',text)
                        for tab in ['Обзор','Компьютер','Рынки','Календарь','Фото','Ассистент']:
                            page.get_by_role('button',name=tab,exact=True).click()
                            assert page.get_by_role('main',name=tab,exact=True).is_visible()
                            assert page.locator('.dashboard-nav-item[aria-current="page"]').count()==1
                            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth + 1')
                            assert page.locator('.dashboard-nav-item').evaluate_all('items=>items.every(b=>b.getBoundingClientRect().height>=44)')
                            count+=1
                        if text==100 and dpr==1:
                            page.get_by_role('button',name='Обзор',exact=True).click()
                            page.screenshot(path=str(evidence/f'{width}-{height}-{"light" if light else "dark"}.png'))
                assert not errors,errors
                context.close()
        browser.close()
        print(f'{count} shell layout cases passed; synthetic/unconfigured data only')
finally:
    pass
