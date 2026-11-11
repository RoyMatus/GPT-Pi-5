// Synthetic font/geometry contract; optional CDP target must be an isolated test browser.
import assert from 'node:assert/strict';
import {createRequire} from 'node:module';
import path from 'node:path';
import {writeFile,mkdir} from 'node:fs/promises';
import {fixture,fixedTime} from './theme-fixtures.mjs';
const require=createRequire(import.meta.url);
const {chromium}=process.env.GPT_PI_PLAYWRIGHT_PATH?require(process.env.GPT_PI_PLAYWRIGHT_PATH):await import('playwright');
const browser=process.env.GPT_PI_CDP_URL?await chromium.connectOverCDP(process.env.GPT_PI_CDP_URL):await chromium.launch({channel:process.env.GPT_PI_TEST_BROWSER_CHANNEL||undefined});
const context=await browser.newContext({viewport:{width:720,height:1280},timezoneId:'Europe/Moscow',reducedMotion:'reduce'});
try {
 const page=await context.newPage();await page.clock.setFixedTime(new Date(fixedTime));
 await page.addInitScript(()=>localStorage.setItem('gpt-pi-scheme','green_phosphor'));
 await page.route('**/*',async route=>{const u=new URL(route.request().url());assert.equal(u.hostname,'127.0.0.1');const data=fixture(u,true);if(data)return route.fulfill({json:data});assert(!u.pathname.startsWith('/api/'));return route.fulfill({path:path.resolve('src/gpt_pi/web',u.pathname==='/'?'index.html':'.'+u.pathname)});});
 await page.goto('http://127.0.0.1:8874/?dashboard');await page.locator('.dashboard-clock').waitFor();await page.evaluate(()=>document.fonts.ready);
 const result=await page.locator('.dashboard-clock').evaluate(async el=>{const style=getComputedStyle(el);await document.fonts.load(`20px ${style.fontFamily}`);const c=document.createElement('canvas').getContext('2d');c.font=`20px ${style.fontFamily}`;return {family:style.fontFamily,digitWidth:c.measureText('0123456789').width,overflow:document.documentElement.scrollWidth>innerWidth};});
 assert(Math.abs(result.digitWidth-109.9609375)<.2,`Consolas-compatible digit advance required: ${JSON.stringify(result)}`);assert(!result.overflow);
 // The fallback must keep the overview network value/detail on one row.
 await page.getByRole('button',{name:'Настройки',exact:true}).click();await page.getByRole('combobox',{name:'Графическая схема',exact:true}).selectOption('fluent_light');await page.getByRole('button',{name:'Готово',exact:true}).click();await page.locator('.dashboard-metric-detail').first().waitFor();await page.evaluate(()=>document.fonts.ready);
 const detail=page.locator('.dashboard-metric-detail').filter({hasText:'↑ 4,2 Мбит/с'});const row=detail.locator('..');
 assert(await row.evaluate(el=>{const [a,b]=el.children;const x=a.getBoundingClientRect(),y=b.getBoundingClientRect();return y.top<x.bottom&&y.bottom>x.top;}),'Network detail must retain reference row at 720px');
 await page.getByRole('button',{name:'Настройки',exact:true}).click();await page.getByRole('combobox',{name:'Графическая схема',exact:true}).selectOption('green_phosphor');await page.getByRole('button',{name:'Готово',exact:true}).click();await page.evaluate(()=>document.fonts.ready);
 const cdp=await context.newCDPSession(page);await cdp.send('DOM.enable');await cdp.send('CSS.enable');const d=await cdp.send('DOM.getDocument');result.fonts=[];
 for(const selector of ['.dashboard-header h1','.dashboard-clock']){const n=await cdp.send('DOM.querySelector',{nodeId:d.root.nodeId,selector});result.fonts.push({selector,...await cdp.send('CSS.getPlatformFontsForNode',{nodeId:n.nodeId})});}
 if(await page.evaluate(()=>navigator.platform.includes('Linux'))) {assert(result.fonts[0].fonts.some(f=>f.familyName==='Cantarell'));assert(result.fonts[1].fonts.some(f=>f.familyName==='Noto Sans Mono'));}
 await mkdir('build',{recursive:true});await writeFile('build/theme-target-fonts.json',JSON.stringify(result,null,2));console.log('PASS: target fonts, numeric advance and viewport',JSON.stringify(result));
}finally{await context.close();await browser.close();}
