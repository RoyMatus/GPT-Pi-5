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
const output=path.join(root,'build/fluent-theme-renders');
await mkdir(output,{recursive:true});
const ids=['fluent_light','fluent_dark','classic','monokai','gruvbox','vscode','dracula','nord','solarized_light','solarized_dark','github_light','tokyo_night','catppuccin','synthwave_84','green_phosphor'];
const tabs=[['overview','Обзор'],['computer','Компьютер'],['markets','Рынки'],['calendar','Календарь'],['photos','Фото'],['assistant','Ассистент']];
const browser = await chromium.launch({channel: process.env.GPT_PI_TEST_BROWSER_CHANNEL || undefined});
const errors=[],report={synthetic:true,schemes:ids,screenshots:[],layoutCases:0,contrast:[]};
async function makePage({authenticated=true,width=720,height=1280,initial,blocked=false,search='?dashboard'}={}) {
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
  await page.goto('http://127.0.0.1:8874/'+search);
  await page.locator('.dashboard-viewport:not([data-portal-node])').waitFor();
  await page.getByText('Демо-город',{exact:true}).waitFor();
  return page;
}
async function select(page,id) {
  await page.getByRole('button',{name:'Обзор',exact:true}).click();
  await page.getByRole('button',{name:'Настройки',exact:true}).click();
  await page.getByRole('combobox',{name:'Графическая схема',exact:true}).selectOption(id);
  assert.equal(await page.locator('.dashboard-viewport:not([data-portal-node])').getAttribute('data-theme'),id);
  assert.equal(await page.evaluate(()=>localStorage.getItem('gpt-pi-scheme')),id);
  assert(await page.locator('.dashboard[data-portal-node]').evaluateAll(nodes=>nodes.every(el=>getComputedStyle(el).backgroundColor==='rgba(0, 0, 0, 0)')),'Portal wrapper must not obscure the underlying screen');
}
async function closeSettings(page) {await page.getByRole('dialog').getByRole('button',{name:'Готово',exact:true}).click();}
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
    const rgba=s=>{const v=(s.match(/[\d.]+/g)||[]).map(Number);return [v[0]/255,v[1]/255,v[2]/255,v[3]??1];};
    const lum=c=>c.slice(0,3).map(v=>v<=.04045?v/12.92:((v+.055)/1.055)**2.4).reduce((a,v,i)=>a+v*[.2126,.7152,.0722][i],0);
    const ratio=(a,b)=>(Math.max(lum(a),lum(b))+.05)/(Math.min(lum(a),lum(b))+.05);
    const fg=rgba(getComputedStyle(el).color),layers=[];
    for(let p=el;p;p=p.parentElement){const style=getComputedStyle(p),color=rgba(style.backgroundColor);layers.push(color);if(color[3]>=1)break;}
    const paint=backdrop=>{let bg=backdrop;for(const c of layers.toReversed())bg=c.slice(0,3).map((v,i)=>v*c[3]+bg[i]*(1-c[3]));const ink=fg.slice(0,3).map((v,i)=>v*fg[3]+bg[i]*(1-fg[3]));return ratio(ink,bg);};
    // A portaled/frosted layer may sit over any content. Bound it against both
    // black and white backdrops instead of treating its rgba value as opaque.
    return Math.min(paint([0,0,0]),paint([1,1,1]));
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
    await closeSettings(page);
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
    await page.reload();await page.locator('.dashboard-viewport:not([data-portal-node])').waitFor();
    assert.equal(await page.locator('.dashboard-viewport:not([data-portal-node])').getAttribute('data-theme'),id);
    await select(guest,id);await closeSettings(guest);
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
      await select(page,id);await closeSettings(page);
      for(const[tab,label]of tabs) {await page.getByRole('button',{name:label,exact:true}).click();await geometry(page,id,tab);}
    }
  }
  for(const mode of ['light','dark']) {
    const migrated=await makePage({initial:{'gpt-pi-theme':mode}});
    assert.equal(await migrated.locator('.dashboard-viewport:not([data-portal-node])').getAttribute('data-theme'),'fluent_'+mode);
    assert.equal(await migrated.locator('.dashboard-viewport:not([data-portal-node])').evaluate(el=>getComputedStyle(el).colorScheme),mode);
    await migrated.context().close();
  }
  const invalid=await makePage({initial:{'gpt-pi-scheme':'broken','gpt-pi-theme':'dark'}});
  assert.equal(await invalid.locator('.dashboard-viewport:not([data-portal-node])').getAttribute('data-theme'),'fluent_dark');await invalid.context().close();
  const blocked=await makePage({blocked:true});
  await blocked.getByRole('button',{name:'Настройки',exact:true}).click();
  await blocked.getByRole('combobox',{name:'Графическая схема',exact:true}).selectOption('nord');
  assert.equal(await blocked.locator('.dashboard-viewport:not([data-portal-node])').getAttribute('data-theme'),'nord');await blocked.context().close();
  const warning=await makePage({authenticated:false,initial:{'gpt-pi-scheme':'green_phosphor'},search:'?dashboard&error=connection'});
  await warning.getByRole('button',{name:'Ассистент',exact:true}).click();
  await warning.locator('.fui-MessageBar').waitFor();
  assert(await warning.locator('.fui-MessageBar').evaluate(el=>{const c=getComputedStyle(el).backgroundColor.match(/[\d.]+/g).map(Number);return c[1]>c[0]&&c[1]>c[2];}),'Phosphor warning must remain green');
  await contrast(warning,'.fui-MessageBarBody','green_phosphor');
  await warning.context().close();
  // Chromium exposes the user's transparency preference through its media emulation.
  const cdp=await page.context().newCDPSession(page);
  await cdp.send('Emulation.setEmulatedMedia',{features:[{name:'prefers-reduced-transparency',value:'reduce'}]});
  assert(await page.evaluate(()=>matchMedia('(prefers-reduced-transparency: reduce)').matches));
  assert.equal(await page.locator('.dashboard-shell > .dashboard-nav').evaluate(el=>getComputedStyle(el).backdropFilter),'none');
  await cdp.send('Emulation.setEmulatedMedia',{features:[]});
  await page.emulateMedia({forcedColors:'active'});
  assert.equal(await page.locator('.dashboard-shell > .dashboard-nav').evaluate(el=>getComputedStyle(el).backdropFilter),'none');
  await page.emulateMedia({forcedColors:'none'});
  report.materialFallbacks=true;report.monochromeWarnings=true;
  assert.deepEqual(errors,[]);
  report.passed=true;await writeFile(path.join(output,'verification.json'),JSON.stringify(report,null,2));
  console.log(`PASS ${report.layoutCases} layout cases; ${report.screenshots.length} actual UI renders; no external network.`);
} finally {await browser.close();}
