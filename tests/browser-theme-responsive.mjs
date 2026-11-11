// Offline responsive audit of the frozen preview UI. Never replaces preview images.
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { createRequire } from 'node:module';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { schemes } from '../frontend/themes.mjs';
import { fixture, fixedTime } from './theme-fixtures.mjs';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const require = createRequire(import.meta.url);
const { chromium } = process.env.GPT_PI_PLAYWRIGHT_PATH
  ? require(process.env.GPT_PI_PLAYWRIGHT_PATH) : await import('playwright');
const tabs = [['overview','Обзор'],['computer','Компьютер'],['markets','Рынки'],['calendar','Календарь'],['photos','Фото'],['assistant','Ассистент']];
const normal = [[320,568],[390,844],[479,800],[480,800],[481,800],
  [599,960],[600,960],[601,960],[719,1280],[720,1280],[721,1280],[800,1280],
  [1023,768],[1024,768],[1025,768],[1280,800],[1920,1080],[2560,1440],[3840,2160],
  [568,320],[640,360],[1280,360]];
const configurations = [
  ...normal.map(([width,height])=>({width,height,dpr:1,text:100})),
  {width:320,height:568,dpr:3,text:100},
  {width:720,height:1280,dpr:2,text:100},
  {width:1280,height:800,dpr:2,text:100},
  {width:3840,height:2160,dpr:2,text:100},
  ...[[390,844],[720,1280],[1280,800]].map(([width,height])=>({width,height,dpr:1,text:200})),
];
const output = path.resolve(root,process.env.GPT_PI_RESPONSIVE_OUTPUT || 'build/theme-responsive-report.json');
const report = {
  schema:1,synthetic:true,kind:'finite-responsive-audit',
  capturedAt:new Date().toISOString(),configurations,schemes:schemes.map(s=>s.id),
  appJsSha256:createHash('sha256').update(await readFile(path.join(root,'src/gpt_pi/web/assets/app.js'))).digest('hex'),
  scope:'Six populated tabs, appearance dialog, guest sign-in; root text scaling is not browser zoom. No screenshots or design changes.',
  limitations:'Finite browser geometry/reachability audit; not all possible screens, pixel fidelity, full accessibility, hardware or Pi performance certification.',
  cases:[],browserErrors:[],externalRequests:[],passed:false,
};
const browser = process.env.GPT_PI_CDP_URL ? await chromium.connectOverCDP(process.env.GPT_PI_CDP_URL) : await chromium.launch({channel:process.env.GPT_PI_TEST_BROWSER_CHANNEL || undefined});
report.browserVersion=browser.version();
async function pageFor(context,authenticated) {
  const page=await context.newPage();page.setDefaultTimeout(3000);
  page.on('pageerror',error=>report.browserErrors.push(error.message));
  await page.clock.setFixedTime(new Date(fixedTime));
  await page.route('**/*',async route=>{
    const url=new URL(route.request().url());
    if(url.hostname!=='127.0.0.1') {report.externalRequests.push(url.origin+url.pathname);return route.abort();}
    const data=fixture(url,authenticated);
    if(data) return route.fulfill({json:data});
    if(url.pathname.startsWith('/api/')) {report.browserErrors.push('Unmocked API '+url.pathname);return route.abort();}
    return route.fulfill({path:path.join(root,'src/gpt_pi/web',url.pathname==='/'?'index.html':url.pathname)});
  });
  return page;
}
async function reset(page,id,config) {
  await page.bringToFront();
  if(page.url()==='about:blank') await page.goto('http://127.0.0.1:8874/?dashboard');
  await page.evaluate(id=>localStorage.setItem('gpt-pi-scheme',id),id);
  await page.goto('http://127.0.0.1:8874/?dashboard');
  await page.locator('.dashboard-viewport:not([data-portal-node])').waitFor();
  await page.getByText('Демо-город',{exact:true}).waitFor({state:'attached',timeout:7000});
  await page.evaluate(text=>document.documentElement.style.fontSize=text+'%',config.text);
  assert.equal(await page.locator('.dashboard-viewport:not([data-portal-node])').getAttribute('data-theme'),id);
}
async function check(record,name,operation) {
  try {await operation();record.checks.push(name);}
  catch(error) {record.failures.push({check:name,message:String(error.message).split('\n').slice(0,8).join('\n')});}
}
async function baseGeometry(page,record,dialog=false) {
  await check(record,'no-page-horizontal-overflow',async()=>assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1)));
  if(!dialog) {
    await check(record,'no-main-horizontal-overflow',async()=>assert(await page.locator('.dashboard-shell > .dashboard-content').evaluate(el=>el.scrollWidth<=el.clientWidth+1)));
    await check(record,'one-current-tab',async()=>assert.equal(await page.locator('.dashboard-nav-item[aria-current="page"]').count(),1));
    await check(record,'navigation-targets-44px',async()=>assert(await page.locator('.dashboard-nav-item').evaluateAll(items=>items.every(el=>el.getBoundingClientRect().height>=44))));
  } else {
    await check(record,'dialog-fits-viewport',async()=>assert(await page.getByRole('dialog').evaluate(el=>{const b=el.getBoundingClientRect();return b.left>=-1&&b.right<=innerWidth+1&&b.top>=-1&&b.bottom<=innerHeight+1;})));
  }
}
async function reachable(record,name,locator) {
  await check(record,name,()=>locator.click({trial:true,timeout:2500}));
}
function newRecord(scheme,config,screen) {
  const record={scheme,config:`${config.width}x${config.height}@${config.dpr}/text${config.text}`,screen,checks:[],failures:[]};
  report.cases.push(record);return record;
}
try {
  for(const config of configurations) {
    const context=await browser.newContext({viewport:{width:config.width,height:config.height},deviceScaleFactor:config.dpr,timezoneId:'Europe/Moscow',reducedMotion:'reduce'});
    const page=await pageFor(context,true),guest=await pageFor(context,false);
    for(const {id} of schemes) {
      await reset(page,id,config);
      for(const[tab,label]of tabs) {
        const record=newRecord(id,config,tab);
        await check(record,'navigate',()=>page.getByRole('button',{name:label,exact:true}).click());
        await check(record,'active-content',()=>page.getByRole('main',{name:label,exact:true}).waitFor());
        await baseGeometry(page,record);
        if(tab==='overview') await reachable(record,'weather-location-action',page.getByRole('button',{name:'Выбрать город',exact:true}));
        if(tab==='computer') await reachable(record,'configure-computer-action',page.getByRole('button',{name:'Настроить компьютер',exact:true}));
        if(tab==='markets') await reachable(record,'last-watchlist-row',page.locator('.dashboard-watchlist-row').last());
        if(tab==='calendar') await reachable(record,'add-calendar-event',page.getByRole('button',{name:'Добавить событие',exact:true}));
        if(tab==='photos') await reachable(record,'start-slideshow',page.getByRole('button',{name:'Начать слайд-шоу',exact:true}));
        if(tab==='assistant') {
          await reachable(record,'message-input',page.locator('textarea'));
          await reachable(record,'audio-check-action',page.getByRole('button',{name:'Проверить звук',exact:true}));
        }
      }
      const settings=newRecord(id,config,'settings');
      await check(settings,'open-settings',async()=>{
        await page.getByRole('button',{name:'Обзор',exact:true}).click();
        await page.getByRole('button',{name:'Настройки',exact:true}).click();
        await page.getByRole('dialog').waitFor();
      });
      await baseGeometry(page,settings,true);
      await reachable(settings,'theme-select',page.getByRole('dialog').getByRole('combobox',{name:'Графическая схема',exact:true}));
      await check(settings,'close-settings',()=>page.getByRole('dialog').getByRole('button',{name:'Готово',exact:true}).click());
      await page.keyboard.press('Escape');
      await reset(guest,id,config);
      const signin=newRecord(id,config,'signin');
      await check(signin,'open-signin',()=>guest.getByRole('button',{name:'Ассистент',exact:true}).click());
      await baseGeometry(guest,signin);
      await reachable(signin,'chatgpt-signin-action',guest.getByRole('button',{name:'Continue with ChatGPT',exact:true}));
      await reachable(signin,'guest-audio-check-action',guest.getByRole('button',{name:'Проверить звук',exact:true}));
    }
    await context.close();
    const cases=report.cases.filter(r=>r.config===`${config.width}x${config.height}@${config.dpr}/text${config.text}`);
    console.log(`${cases.filter(r=>!r.failures.length).length}/${cases.length} passed: ${config.width}x${config.height} DPR ${config.dpr} text ${config.text}%`);
    await mkdir(path.dirname(output),{recursive:true});
    await writeFile(output,JSON.stringify(report,null,2)+'\n');
  }
} catch(error) {report.fatal=String(error.stack||error);}
finally {
  await browser.close();
  report.caseCount=report.cases.length;
  report.failedCases=report.cases.filter(r=>r.failures.length).length;
  report.passed=!report.fatal&&!report.failedCases&&!report.browserErrors.length&&!report.externalRequests.length;
  await mkdir(path.dirname(output),{recursive:true});
  await writeFile(output,JSON.stringify(report,null,2)+'\n');
  console.log(`${report.caseCount-report.failedCases}/${report.caseCount} responsive cases passed; report: ${output}`);
  if(!report.passed) process.exitCode=1;
}
