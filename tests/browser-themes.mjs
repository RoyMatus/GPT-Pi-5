// Production UI with intercepted synthetic data. No real backend/account/API.
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import { mkdir,writeFile } from 'node:fs/promises';
import { fixture,fixedTime } from './theme-fixtures.mjs';
const require = createRequire(import.meta.url);
const { chromium } = process.env.GPT_PI_PLAYWRIGHT_PATH
  ? require(process.env.GPT_PI_PLAYWRIGHT_PATH) : await import('playwright');
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const output=path.join(root,'build/theme-renders');
await mkdir(output,{recursive:true});
const ids=['classic','monokai','gruvbox','vscode','dracula','nord','solarized_light','solarized_dark','github_light','tokyo_night','catppuccin','synthwave_84'];
const tabs=[['overview','Обзор'],['computer','Компьютер'],['markets','Рынки'],['calendar','Календарь'],['photos','Фото'],['assistant','Ассистент']];
const browser = await chromium.launch({channel: process.env.GPT_PI_TEST_BROWSER_CHANNEL || undefined});
const errors=[],report={synthetic:true,schemes:ids,screenshots:[],layoutCases:0,contrast:[]};
async function makePage({authenticated=true,width=720,height=1280,initial,blocked=false}={}) {
  const context=await browser.newContext({viewport:{width,height},timezoneId:'Europe/Moscow',reducedMotion:'reduce'});
  const page=await context.newPage();page.setDefaultTimeout(7000);
  page.on('pageerror',error=>errors.push(error.message));
  await page.clock.setFixedTime(new Date(fixedTime));
  if(initial) await page.addInitScript(state=>{for(const[k,v]of Object.entries(state))localStorage.setItem(k,v);},initial);
  if(blocked) await page.addInitScript(()=>Object.defineProperty(window,'localStorage',{get(){throw new DOMException('Denied','SecurityError');}}));
  await page.route('**/*',async route=>{
    const url=new URL(route.request().url());
    assert.equal(url.hostname,'127.0.0.1','External request forbidden');
    const data=fixture(url,authenticated);
    if(data) return route.fulfill({json:data});
    if(url.pathname.startsWith('/api/')) throw new Error('Unmocked API '+url.pathname);
    const file=path.join(root,'src/gpt_pi/web',url.pathname==='/'?'index.html':url.pathname);
    await route.fulfill({path:file});
  });
  await page.goto('http://127.0.0.1:8874/?dashboard');
  await page.locator('.dashboard-viewport').waitFor();
  await page.getByText('Демо-город',{exact:true}).waitFor();
  return page;
}
async function select(page,id) {
  await page.getByRole('button',{name:'Обзор',exact:true}).click();
  await page.getByRole('button',{name:'Настройки',exact:true}).click();
  await page.getByRole('combobox',{name:'Графическая схема',exact:true}).selectOption(id);
  assert.equal(await page.locator('.dashboard-viewport').getAttribute('data-theme'),id);
  assert.equal(await page.evaluate(()=>localStorage.getItem('gpt-pi-scheme')),id);
}
async function shot(page,id,screen) {
  await page.screenshot({path:path.join(output,`${id}-${screen}.png`),animations:'disabled'});
  report.screenshots.push(`${id}-${screen}.png`);
}
async function geometry(page,id,tab) {
  assert.equal(await page.locator('.dashboard-nav-item[aria-current="page"]').count(),1);
  assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),`${id}/${tab}: page overflow`);
  assert(await page.locator('.dashboard-nav-item').evaluateAll(items=>items.every(b=>b.getBoundingClientRect().height>=44)),`${id}/${tab}: touch targets`);
  report.layoutCases++;
}
async function contrast(page,selector,id) {
  const ratios=await page.locator(selector).evaluateAll(items=>items.filter(el=>el.getBoundingClientRect().height).map(el=>{
    const rgb=s=>(s.match(/[\d.]+/g)||[]).slice(0,3).map(Number).map(v=>v/255);
    const lum=c=>c.map(v=>v<=.04045?v/12.92:((v+.055)/1.055)**2.4).reduce((a,v,i)=>a+v*[.2126,.7152,.0722][i],0);
    let bg='';for(let p=el;p;p=p.parentElement){const b=getComputedStyle(p).backgroundColor;if(b!=='rgba(0, 0, 0, 0)'&&b!=='transparent'){bg=b;break;}}
    const a=lum(rgb(getComputedStyle(el).color)),b=lum(rgb(bg));return(Math.max(a,b)+.05)/(Math.min(a,b)+.05);
  }));
  assert(ratios.length,`${id}: missing contrast element ${selector}`);
  for(const ratio of ratios) assert(ratio>=4.5,`${id} ${selector} contrast ${ratio.toFixed(2)}`);
  report.contrast.push({id,selector,minimum:Math.min(...ratios)});
}
try {
  const page=await makePage();
  const guest=await makePage({authenticated:false});
  for(const id of ids) {
    await select(page,id);
    await shot(page,id,'settings');
    await page.getByRole('button',{name:'Настройки',exact:true}).click();
    for(const[tab,label]of tabs) {
      await page.getByRole('button',{name:label,exact:true}).click();
      await page.getByRole('main',{name:label,exact:true}).waitFor();
      if(tab==='computer') await page.getByText('54 °C',{exact:true}).waitFor();
      if(tab==='markets') await page.getByRole('button',{name:'1W',exact:true}).waitFor();
      if(tab==='calendar') await page.getByRole('button',{name:'Добавить событие'}).waitFor();
      if(tab==='photos') await page.getByText('Доступно фотографий: 1',{exact:true}).waitFor();
      if(tab==='assistant') await page.getByRole('region',{name:'Переписка'}).waitFor();
      await geometry(page,id,tab);
      await shot(page,id,tab);
      if(tab==='calendar') {
        await page.getByRole('button',{name:'Добавить событие'}).click();
        const dialog=page.getByRole('dialog');await dialog.getByLabel('Название',{exact:true}).fill('Новая идея');
        await contrast(page,'.fui-DialogTitle',id);await shot(page,id,'event-dialog');
        await dialog.getByRole('button',{name:'Отмена',exact:true}).click();
      }
    }
    await contrast(page,'.message-text',id);
    await contrast(page,'.message.assistant .fui-Avatar__initials',id);
    await page.getByRole('button',{name:'Настройки',exact:true}).click();
    assert.equal(await page.getByRole('dialog').getByRole('combobox',{name:'Графическая схема',exact:true}).inputValue(),id);
    await contrast(page,'.fui-DialogTitle',id);await shot(page,id,'assistant-settings');
    await page.getByRole('dialog').getByRole('button',{name:'Готово',exact:true}).click();
    await page.reload();await page.locator('.dashboard-viewport').waitFor();
    assert.equal(await page.locator('.dashboard-viewport').getAttribute('data-theme'),id);
    await select(guest,id);await guest.getByRole('button',{name:'Настройки',exact:true}).click();
    await guest.getByRole('button',{name:'Ассистент',exact:true}).click();
    await guest.getByRole('button',{name:'Continue with ChatGPT',exact:true}).waitFor();
    await contrast(guest,'.signin-heading strong',id);await contrast(guest,'.signin-card > button',id);await shot(guest,id,'signin');
    await guest.getByRole('button',{name:'Проверить звук',exact:true}).click();
    await guest.getByRole('dialog').waitFor();await contrast(guest,'.fui-DialogTitle',id);await shot(guest,id,'audio-dialog');
    // Style probe inside the actual portal; no physical microphone permission.
    await guest.getByRole('dialog').evaluate(el=>{const probe=document.createElement('span');probe.className='recording-label theme-recording-probe';probe.textContent='● Идёт запись';el.append(probe);});
    await contrast(guest,'.theme-recording-probe',id);
    await guest.locator('.theme-recording-probe').evaluate(el=>el.remove());
    await guest.getByRole('dialog').getByRole('button',{name:'Закрыть проверку',exact:true}).click();
    console.log(`PASS ${id}: six screens, settings, sign-in, portal dialogs, persistence`);
  }
  for(const[width,height]of[[390,844],[1280,800]]) {
    await page.setViewportSize({width,height});
    for(const id of ids) {
      await select(page,id);await page.getByRole('button',{name:'Настройки',exact:true}).click();
      for(const[tab,label]of tabs) {await page.getByRole('button',{name:label,exact:true}).click();await geometry(page,id,tab);}
    }
  }
  for(const mode of ['light','dark']) {
    const migrated=await makePage({initial:{'gpt-pi-theme':mode}});
    assert.equal(await migrated.locator('.dashboard-viewport').getAttribute('data-theme'),'fluent');
    assert.equal(await migrated.locator('.dashboard-viewport').evaluate(el=>getComputedStyle(el).colorScheme),mode);
    await migrated.context().close();
  }
  const invalid=await makePage({initial:{'gpt-pi-scheme':'broken','gpt-pi-theme':'dark'}});
  assert.equal(await invalid.locator('.dashboard-viewport').getAttribute('data-theme'),'fluent');await invalid.context().close();
  const blocked=await makePage({blocked:true});
  await blocked.getByRole('button',{name:'Настройки',exact:true}).click();
  await blocked.getByRole('combobox',{name:'Графическая схема',exact:true}).selectOption('nord');
  assert.equal(await blocked.locator('.dashboard-viewport').getAttribute('data-theme'),'nord');await blocked.context().close();
  assert.deepEqual(errors,[]);
  report.passed=true;await writeFile(path.join(output,'verification.json'),JSON.stringify(report,null,2));
  console.log(`PASS ${report.layoutCases} layout cases; ${report.screenshots.length} actual UI renders; no external network.`);
} finally {await browser.close();}
