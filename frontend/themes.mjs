// Menu colors and finishes from Swypetris menu_ui_tokens.json; layout remains GPT-Pi 5.
import sourceThemes from './themes-data.json' with { type: 'json' };

const descriptions = {
  classic: 'Ранние цветные ПК: тёмно-синее поле, кремовые рамки и чёткие углы.',
  monokai: 'Цветной синтаксис: угольный фон, лайм и небольшие яркие акценты.',
  gruvbox: 'Тёплая мастерская: кремовый текст, оливковый акцент и двойная рамка.',
  vscode: 'Рабочий редактор: нейтральный графит, мятный акцент и спокойные поверхности.',
  dracula: 'Ночная готика: чернильный фон, лиловые детали и холодный голубой свет.',
  nord: 'Северный иней: сине-серые поверхности, ледяной акцент и мягкие блики.',
  solarized_light: 'Светлая бумага: тёплый фон, глубокий текст и сдержанная бирюза.',
  solarized_dark: 'Глубокий петроль: сине-зелёный фон, светлый текст и ясная бирюза.',
  github_light: 'Чистый лист: белое поле, лёгкие серые карточки и синий акцент.',
  tokyo_night: 'Дождливый город: ночной индиго, голубые линии и лиловые отражения.',
  catppuccin: 'Мягкий сатин: тёмная основа и спокойные пастельные оттенки.',
  synthwave_84: 'Аркада 1984: фиолетовый фон, электрический циан и тонкие линии экрана.',
};
const names = { classic: 'Classic', vscode: 'VSCode', catppuccin: 'Catppuccin', synthwave_84: "Synthwave '84" };
const positive = { classic:'#36CB89', monokai:'#A6E22E', gruvbox:'#B8BB26', vscode:'#8FCB82', dracula:'#50FA7B', nord:'#A3BE8C', solarized_light:'#397024', solarized_dark:'#9CB943', github_light:'#1A7F37', tokyo_night:'#9ECE6A', catppuccin:'#A6E3A1', synthwave_84:'#72F1B8' };
export const schemes = [
  { id:'fluent', name:'Fluent', description:'Исходное оформление GPT-Pi 5. Светлый и тёмный режимы.', finish:'fluent' },
  ...sourceThemes.map(theme=>({...theme, name:names[theme.id]||theme.title, description:descriptions[theme.id], positive:positive[theme.id]})),
];
const lightFluent = { light:true, background:'#F7F9FC', panel:'#FFFFFF', text:'#242424', muted:'#4D5968', border:'#C7CDD6', control:'#0969DA', onControl:'#FFFFFF', focus:'#005A9E', positive:'#187542', roles:{settings:'#0969DA',destructive:'#B42332',link:'#0969DA'}, radiusDp:14, strokeDp:1 };
const darkFluent = { light:false, background:'#111922', panel:'#1B2530', text:'#F6F7FB', muted:'#BDC8D6', border:'#43505E', control:'#63D8FF', onControl:'#111922', focus:'#A6E7FF', positive:'#58F29D', roles:{settings:'#24D5E7',destructive:'#FF7C79',link:'#63D8FF'}, radiusDp:14, strokeDp:1 };

export function resolveAppearance(schemeId, legacyMode = 'light') {
  const scheme = schemes.find(item=>item.id===schemeId)||schemes[0];
  return scheme.id==='fluent' ? {...scheme, ...(legacyMode==='dark'?darkFluent:lightFluent)} : scheme;
}

export function readAppearance(storage) {
  try {
    const saved = storage ?? globalThis.localStorage;
    return resolveAppearance(saved?.getItem('gpt-pi-scheme'), saved?.getItem('gpt-pi-theme'));
  } catch { return resolveAppearance('fluent'); }
}

export function saveAppearance(storage, appearance) {
  try {
    const saved = storage ?? globalThis.localStorage;
    saved?.setItem('gpt-pi-scheme', appearance.id);
    if (appearance.id==='fluent') saved?.setItem('gpt-pi-theme',appearance.light?'light':'dark');
    return true;
  } catch { return false; }
}

// Derived surface tones avoid translucent text and preserve a single solid reading surface.
export function mixColors(a, b, amount) {
  const values = color=>color.slice(1).match(/../g).map(value=>parseInt(value,16));
  return '#'+values(a).map((value,i)=>Math.round(value*(1-amount)+values(b)[i]*amount).toString(16).padStart(2,'0')).join('');
}

function contrastRatio(a, b) {
  const luminance = color=>color.slice(1).match(/../g)
    .map(value=>parseInt(value,16)/255)
    .map(value=>value<=.04045?value/12.92:((value+.055)/1.055)**2.4)
    .reduce((sum,value,index)=>sum+value*[.2126,.7152,.0722][index],0);
  const first=luminance(a), second=luminance(b);
  return (Math.max(first,second)+.05)/(Math.min(first,second)+.05);
}

// Source destructive colors are preserved in the data. Small status text needs
// a readable variant on every surface where recording/error labels can appear.
function statusColor(theme, selected) {
  const surfaces=[theme.background,theme.panel,selected];
  for(let step=0;step<=100;step++) {
    const color=mixColors(theme.roles.destructive,theme.text,step/100);
    if(surfaces.every(surface=>contrastRatio(color,surface)>=4.5)) return color;
  }
  return theme.text;
}

export function appearanceVariables(theme) {
  const selected=mixColors(theme.panel,theme.control,.16);
  return {
    '--scheme-bg':theme.background, '--scheme-panel':theme.panel,
    '--scheme-raised':mixColors(theme.panel,theme.text,.055),
    '--scheme-text':theme.text, '--scheme-muted':theme.muted,
    '--scheme-border':theme.border, '--scheme-divider':mixColors(theme.panel,theme.border,.3),
    '--scheme-control':theme.control, '--scheme-on-control':theme.onControl,
    '--scheme-secondary':theme.roles.settings, '--scheme-positive':theme.positive,
    '--scheme-negative':statusColor(theme,selected), '--scheme-link':theme.roles.link,
    '--scheme-focus':theme.focus, '--scheme-selected':selected,
    '--scheme-radius':theme.radiusDp+'px', '--scheme-stroke':theme.strokeDp+'px',
    '--scheme-shadow':theme.light?'0 4px 16px #00000008':'0 4px 16px #00000024',
  };
}
