#!/usr/bin/env node
// Compose actual browser captures; never render replacement UI or fetch remote assets.
// Usage: node tools/render-theme-gallery.mjs [--dir build/theme-renders]
// Optional GPT_PI_SHARP_PATH points to an existing sharp installation (not a new app dependency).
import { createHash } from 'node:crypto';
import { mkdir, readFile, stat, writeFile } from 'node:fs/promises';
import { createRequire } from 'node:module';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { schemes } from '../frontend/themes.mjs';

const args = process.argv.slice(2);
if (args.length && (args.length !== 2 || args[0] !== '--dir')) {
  throw new Error('Usage: node tools/render-theme-gallery.mjs [--dir build/theme-renders]');
}
const root = fileURLToPath(new URL('../', import.meta.url));
const directory = path.resolve(root, args[1] ?? 'build/theme-renders');
const require = createRequire(import.meta.url);
let sharp;
try { sharp = require(process.env.GPT_PI_SHARP_PATH || 'sharp'); }
catch (error) {
  throw new Error('The gallery composer needs sharp. Set GPT_PI_SHARP_PATH to an existing installation.', { cause:error });
}

const themes = schemes.filter(theme => theme.id !== 'fluent');
const screens = [
  ['overview','Обзор'], ['computer','Компьютер'], ['markets','Рынки'], ['calendar','Календарь'],
  ['photos','Фото'], ['assistant','Ассистент'], ['settings','Оформление'], ['signin','Вход'],
];
const dialogs = [
  ['event-dialog','Событие календаря'], ['assistant-settings','Настройки ассистента'],
  ['audio-dialog','Проверка звука'],
];
const width = 1504;
const height = 1500;
const tileWidth = 360;
const tileHeight = 640;
const padding = 20;
const columnGap = 8;
const firstLabelTop = 104;
const rowStep = 698;
const labelHeight = 30;
const escape = value => String(value).replace(/[&<>"']/g, character => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[character]));
const hash = data => createHash('sha256').update(data).digest('hex');
const screenshotName = (theme, screen) => `${theme.id}-${screen}.png`;
const sheetName = theme => `${theme.id}-contact-sheet.png`;
const palette = theme => [theme.background,theme.panel,theme.text,theme.control,theme.roles.settings];
const verifiedFiles = new Map();

// Validate the complete capture set before replacing any existing gallery artifact.
for (const theme of themes) {
  for (const [screen] of [...screens,...dialogs]) {
    const name = screenshotName(theme,screen);
    let data;
    try { data = await readFile(path.join(directory,name)); }
    catch (error) { throw new Error(`Capture missing: ${name}. Finish tests/browser-themes.mjs before composing.`, {cause:error}); }
    const metadata = await sharp(data).metadata();
    if (metadata.width !== 720 || metadata.height !== 1280) {
      throw new Error(`${name}: expected a complete 720 × 1280 browser viewport, received ${metadata.width} × ${metadata.height}.`);
    }
    verifiedFiles.set(name,{name,width:720,height:1280,bytes:data.length,sha256:hash(data)});
  }
}

function sheetFrame(theme,index) {
  const chips = palette(theme).map((color,i) => `<rect x="${1288+i*36}" y="31" width="28" height="28" rx="7" fill="${color}" stroke="#c8cfd8" stroke-width="0.7"/>`).join('');
  const labels = screens.map(([screen,label],i) => {
    const x = padding+(i%4)*(tileWidth+columnGap);
    const y = firstLabelTop+Math.floor(i/4)*rowStep;
    return `<rect x="${x-1}" y="${y}" width="362" height="671" rx="5" fill="#d1d8e2"/>
      <rect x="${x}" y="${y}" width="360" height="30" fill="#ffffff"/>
      <text x="${x+12}" y="${y+20}" font-size="13" font-weight="600" fill="#344154">${String(i+1).padStart(2,'0')}  ${escape(label)}</text>`;
  }).join('');
  return Buffer.from(`<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}">
    <style>text{font-family:'Segoe UI','Arial',sans-serif}</style>
    <rect width="${width}" height="${height}" fill="#eef1f6"/>
    <text x="20" y="23" font-size="10" font-weight="600" letter-spacing="1.5" fill="#637084">GPT-Pi 5 / SWYPETRIS COLLECTION</text>
    <text x="20" y="62" font-size="31" font-weight="650" fill="#172334">${escape(theme.name)}</text>
    <text x="20" y="87" font-size="15" fill="#536175">${escape(theme.description)}</text>
    ${chips}${labels}
    <text x="20" y="1490" font-size="10" fill="#637084">Реальный интерфейс • демонстрационные данные • исходные экраны 720 × 1280</text>
    <text x="1484" y="1490" font-size="10" fill="#637084" text-anchor="end">${String(index+1).padStart(2,'0')} / ${themes.length}</text>
  </svg>`);
}

function imageLinks(theme, entries) {
  return entries.map(([id,label]) => `<a href="${screenshotName(theme,id)}" target="_blank" rel="noopener">${escape(label)}<span>720 × 1280 ↗</span></a>`).join('');
}

function galleryHtml() {
  const navigation = themes.map(theme => `<a href="#${theme.id}"><i style="background:${theme.control};border-color:${theme.background}"></i>${escape(theme.name)}</a>`).join('');
  const sections = themes.map((theme,index) => `<section id="${theme.id}" aria-labelledby="${theme.id}-title">
    <header class="theme-header"><div><p class="eyebrow">ТЕМА ${String(index+1).padStart(2,'0')}</p><h2 id="${theme.id}-title">${escape(theme.name)}</h2><p>${escape(theme.description)}</p></div><div class="swatches" aria-label="Основная палитра">${palette(theme).map(color => `<span style="background:${color}" title="${color}"></span>`).join('')}</div></header>
    <a class="sheet" href="${sheetName(theme)}" target="_blank" rel="noopener"><img src="${sheetName(theme)}" width="${width}" height="${height}" alt="${escape(theme.name)}: обзор, компьютер, рынки, календарь, фото, ассистент, оформление и вход" loading="${index===0?'eager':'lazy'}"/></a>
    <details><summary>Открыть экраны в полном размере <span>8 экранов + 3 диалога</span></summary>
      <h3>Экраны</h3><div class="links">${imageLinks(theme,screens)}</div>
      <h3>Диалоги</h3><div class="links">${imageLinks(theme,dialogs)}</div>
    </details>
    <p class="back"><a href="#top">К списку тем ↑</a></p>
  </section>`).join('');
  return `<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>GPT-Pi 5 — 12 тем Swypetris</title>
  <style>
  :root{color-scheme:light;font-family:'Segoe UI',Arial,sans-serif;color:#1b293a;background:#eef1f6;font-synthesis:none}*{box-sizing:border-box}body{margin:0}main{max-width:1544px;margin:auto;padding:40px 20px 24px}a{color:#235f9a;text-decoration:none}a:hover{text-decoration:underline}a:focus-visible,summary:focus-visible{outline:3px solid #0078d4;outline-offset:4px}h1{font-size:clamp(30px,4vw,52px);font-weight:650;letter-spacing:-1.5px;margin:12px 0 16px}h2{font-size:28px;margin:6px 0 10px}p{line-height:1.5}.intro{max-width:850px;font-size:18px;color:#526174}.eyebrow{font-size:11px;letter-spacing:1.5px;font-weight:650;color:#637084;margin:0}.note{font-size:14px;color:#637084;margin-top:20px}nav{display:flex;flex-wrap:wrap;gap:8px;margin:30px 0 48px}nav a{display:flex;align-items:center;gap:9px;padding:11px 15px;border:1px solid #d4dbe5;background:#fff;border-radius:22px;color:#32445b;font-size:14px}nav i{display:block;width:13px;height:13px;border-radius:50%;border:2px solid}section{margin:0 0 60px;scroll-margin-top:20px}.theme-header{display:flex;gap:24px;align-items:center;justify-content:space-between;padding:0 4px 18px}.theme-header p:not(.eyebrow){color:#536175;margin:0}.swatches{display:flex;gap:8px}.swatches span{width:30px;height:30px;border-radius:8px;border:1px solid #c8cfd8}.sheet{display:block;border:1px solid #d5dce6;border-radius:12px;overflow:hidden;background:#fff;box-shadow:0 12px 30px #22354a0a}.sheet img{display:block;width:100%;height:auto}details{margin-top:16px;background:#fff;border:1px solid #d5dce6;border-radius:12px;padding:0 20px 20px}details:not([open]){padding-bottom:0}summary{padding:18px 0;cursor:pointer;font-weight:600;min-height:54px}summary span{font-size:13px;font-weight:400;color:#657387;margin-left:12px}h3{font-size:14px;margin:15px 0 12px}.links{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:8px}.links a{display:flex;justify-content:space-between;gap:8px;align-items:center;background:#f6f8fb;border:1px solid #e2e7ee;border-radius:7px;padding:12px;min-height:44px;font-size:14px}.links span{font-size:10px;color:#637084;white-space:nowrap}.back{text-align:right;font-size:12px}footer{font-size:13px;color:#637084;border-top:1px solid #d1d9e3;padding-top:20px}@media(max-width:800px){main{padding:24px 12px}.theme-header{align-items:flex-start}.links{grid-template-columns:repeat(2,minmax(0,1fr))}.swatches{gap:4px}.swatches span{width:20px;height:20px}.intro{font-size:16px}}@media(max-width:480px){.links{grid-template-columns:1fr}.theme-header{display:block}.swatches{margin-top:15px}summary span{display:block;margin:8px 0 0}nav{gap:6px}nav a{padding:9px 12px;font-size:12px}}
  </style></head><body><main id="top"><p class="eyebrow">ВИЗУАЛЬНАЯ КОЛЛЕКЦИЯ / GPT-Pi 5</p><h1>12 характеров одного интерфейса</h1><p class="intro">Темы Swypetris перенесены в GPT-Pi 5: палитры, материалы и настроение меняются, привычное расположение экранов сохраняется.</p><p class="note">Снимки настоящего интерфейса с демонстрационными данными. Каждый экран доступен в исходном размере 720 × 1280. Галерея полностью локальная и работает без подключения к интернету.</p><nav aria-label="Темы оформления">${navigation}</nav>${sections}<footer>12 тем · 96 основных экранов · 36 диалогов · <a href="manifest.json">Состав и контрольные суммы</a> · <a href="verification.json">Результаты проверки интерфейса</a></footer></main></body></html>`;
}

await mkdir(directory,{recursive:true});
const manifest = {schema:1,kind:'actual-ui-screenshot-gallery',syntheticData:true,sourceViewport:{width:720,height:1280},sheet:{width,height,columns:4,rows:2,tileWidth,tileHeight},themes:[]};
for (const [index,theme] of themes.entries()) {
  const composite = [{input:sheetFrame(theme,index),top:0,left:0}];
  for (const [i,[screen]] of screens.entries()) {
    composite.push({input:await sharp(path.join(directory,screenshotName(theme,screen))).resize(tileWidth,tileHeight,{fit:'fill',kernel:'lanczos3'}).png().toBuffer(),left:padding+(i%4)*(tileWidth+columnGap),top:firstLabelTop+Math.floor(i/4)*rowStep+labelHeight});
  }
  const name = sheetName(theme);
  const sheet = await sharp({create:{width,height,channels:3,background:'#eef1f6'}}).composite(composite).png().toBuffer();
  await writeFile(path.join(directory,name),sheet);
  manifest.themes.push({id:theme.id,name:theme.name,description:theme.description,palette:palette(theme),contactSheet:{name,width,height,bytes:sheet.length,sha256:hash(sheet)},screens:screens.map(([id,label])=>({id,label,...verifiedFiles.get(screenshotName(theme,id))})),dialogs:dialogs.map(([id,label])=>({id,label,...verifiedFiles.get(screenshotName(theme,id))}))});
  console.log(`Composed ${name}`);
}
await writeFile(path.join(directory,'manifest.json'),JSON.stringify(manifest,null,2)+'\n','utf8');
await writeFile(path.join(directory,'index.html'),galleryHtml(),'utf8');
const html = await readFile(path.join(directory,'index.html'),'utf8');
for (const match of html.matchAll(/(?:href|src)="([^"#]+)"/g)) {
  if (match[1].startsWith('http')) throw new Error('Gallery must not use network resources.');
  await stat(path.join(directory,match[1]));
}
console.log(`Gallery ready: ${themes.length} sheets, ${verifiedFiles.size} original captures, all local links verified. ${directory}`);
