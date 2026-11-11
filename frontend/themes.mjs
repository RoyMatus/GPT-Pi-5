// Swypetris identities with Fluent 2 surfaces; original menu tokens stay unchanged.
import sourceThemes from './themes-data.json' with { type: 'json' };

const descriptions = {
  classic: 'Насыщенный синий и кремовый текст в спокойных слоях Fluent 2.',
  monokai: 'Цветной синтаксис: угольный фон, лайм и небольшие яркие акценты.',
  gruvbox: 'Тёплый графит, кремовый текст и оливковые акценты на мягких поверхностях.',
  vscode: 'Рабочий редактор: нейтральный графит, мятный акцент и спокойные поверхности.',
  dracula: 'Чернильный фон, лиловая глубина и холодный голубой акцент.',
  nord: 'Северный иней: сине-серые поверхности, ледяной акцент и мягкие блики.',
  solarized_light: 'Светлая бумага: тёплый фон, глубокий текст и сдержанная бирюза.',
  solarized_dark: 'Глубокий петроль: сине-зелёный фон, светлый текст и ясная бирюза.',
  github_light: 'Чистый лист: белое поле, лёгкие серые карточки и синий акцент.',
  tokyo_night: 'Дождливый город: ночной индиго, голубые линии и лиловые отражения.',
  catppuccin: 'Мягкий сатин: тёмная основа и спокойные пастельные оттенки.',
  synthwave_84: 'Фиолетовая глубина и электрический циан с мягким стеклом Fluent 2.',
};
const names = { classic: 'Classic', vscode: 'VSCode', catppuccin: 'Catppuccin', synthwave_84: "Synthwave '84" };
const positive = { classic:'#36CB89', monokai:'#A6E22E', gruvbox:'#B8BB26', vscode:'#8FCB82', dracula:'#50FA7B', nord:'#A3BE8C', solarized_light:'#397024', solarized_dark:'#9CB943', github_light:'#1A7F37', tokyo_night:'#9ECE6A', catppuccin:'#A6E3A1', synthwave_84:'#72F1B8' };
// Neutral/brand values verified against installed Fluent UI React v9 web themes.
const lightFluent = { id:'fluent_light', name:'Fluent 2 Light', description:'Чистая Fluent 2: светлые нейтральные поверхности, синий акцент и мягкая глубина.',isFluent:true,finish:'fluent',light:true,background:'#F5F5F5',panel:'#FFFFFF',text:'#242424',muted:'#424242',border:'#E0E0E0',control:'#0F6CBD',onControl:'#FFFFFF',focus:'#242424',positive:'#107C10',roles:{settings:'#0F6CBD',destructive:'#C50F1F',link:'#0F6CBD'},radiusDp:8,strokeDp:1 };
const darkFluent = { id:'fluent_dark', name:'Fluent 2 Dark', description:'Чистая Fluent 2: нейтральный графит, светлая типографика и синие действия.',isFluent:true,finish:'fluent',light:false,background:'#141414',panel:'#292929',text:'#FFFFFF',muted:'#D6D6D6',border:'#525252',control:'#479EF5',onControl:'#141414',focus:'#FFFFFF',positive:'#54B054',roles:{settings:'#479EF5',destructive:'#FF9AA2',link:'#479EF5'},radiusDp:8,strokeDp:1 };
const greenPhosphor = { id:'green_phosphor',name:'Green Phosphor',description:'Зелёный люминофор: почти чёрный экран, монохромные знаки и спокойное свечение.',finish:'phosphor',light:false,background:'#040D06',panel:'#0A190D',text:'#B6F5C0',muted:'#83BD8D',border:'#32633D',control:'#65E881',onControl:'#040D06',focus:'#B6F5C0',positive:'#65E881',roles:{settings:'#65E881',destructive:'#65E881',link:'#65E881'},radiusDp:8,strokeDp:1 };
export const schemes = [
  lightFluent,darkFluent,
  ...sourceThemes.map(theme=>({...theme,name:names[theme.id]||theme.title,description:descriptions[theme.id],positive:positive[theme.id],radiusDp:8,strokeDp:1})),
  greenPhosphor,
];

export function resolveAppearance(schemeId, legacyMode = 'light') {
  return schemes.find(item=>item.id===schemeId)||(legacyMode==='dark'?darkFluent:lightFluent);
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
    if (appearance.isFluent) saved?.setItem('gpt-pi-theme',appearance.light?'light':'dark');
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
  const rgba=(color,alpha)=>`rgba(${color.slice(1).match(/../g).map(v=>parseInt(v,16)).join(',')},${alpha})`;
  const canvas=theme.isFluent?theme.background:`radial-gradient(ellipse at 0% 0%,${mixColors(theme.background,theme.control,.10)} 0,transparent 62%),radial-gradient(ellipse at 100% 100%,${mixColors(theme.background,theme.roles.settings,.055)} 0,transparent 60%),${theme.background}`;
  return {
    '--scheme-bg':theme.background, '--scheme-panel':theme.panel,
    '--scheme-raised':mixColors(theme.panel,theme.text,.055),
    '--scheme-text':theme.text, '--scheme-muted':theme.muted,
    '--scheme-border':theme.border, '--scheme-divider':mixColors(theme.panel,theme.border,.3),
    '--scheme-control':theme.control, '--scheme-on-control':theme.onControl,
    '--scheme-secondary':theme.roles.settings, '--scheme-positive':theme.positive,
    '--scheme-negative':statusColor(theme,selected), '--scheme-link':theme.roles.link,
    '--scheme-focus':theme.focus, '--scheme-selected':selected,
    '--scheme-canvas':canvas,'--scheme-glass':rgba(theme.panel,.88),'--scheme-glass-strong':rgba(theme.panel,.96),
    '--scheme-edge':mixColors(theme.panel,theme.text,theme.light?.10:.12),'--scheme-wash':mixColors(theme.panel,theme.control,.06),
    '--scheme-font':'"Segoe UI Variable", "Segoe UI", "GPT Pi Sans", system-ui, sans-serif',
    '--scheme-radius':theme.radiusDp+'px', '--scheme-stroke':theme.strokeDp+'px',
    '--scheme-shadow':theme.light?'0 4px 16px #00000008':'0 4px 16px #00000024',
  };
}
