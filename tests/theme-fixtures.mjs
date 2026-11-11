// Deliberately synthetic UI examples, with no backend or external requests.
export const fixedTime = '2026-11-11T11:35:00Z';
const series = [24,31,28,40,37,45,35,50,43,47,38,42];
const quote = (id,label,value,change,category='crypto',currency='USD') => ({
  id,label,value,change,category,currency,provider:'Демо-данные',state:'ready',
  period:'1D',detail:'Пример оформления',quoteTime:'11.11.2026 · 14:35',
  history:series.map((n,i)=>({value:value*(.94+n/800),time:i})),
});
const quotes=[quote('kraken:XBTUSD','BTC / USD',86420,2.34),quote('demo:ETH','ETH / USD',3210,-1.18),quote('demo:INDEX','Индекс',2840,0.72,'index','points'),quote('demo:USD','USD / RUB',92.45,0,'fx','RUB'),quote('demo:EUR','EUR / RUB',100.25,0,'fx','RUB')];
export function fixture(url, authenticated=true) {
  const path=url.pathname;
  if(path==='/api/keyboard') return {visible:false,height:0};
  if(path==='/api/session') return {authenticated,csrf:'synthetic',provider:'chatgpt',registrations:[],remember_login:true,account:authenticated?{name:'Демонстрация',sharing:true}:undefined};
  if(path==='/api/capabilities') return {voice:false};
  if(path==='/api/models') return {models:[{id:'demo-model',name:'Демо-модель'}]};
  if(path==='/api/chats') return {chats:[{id:'demo-chat',title:'Идеи на вечер'}]};
  if(path==='/api/chats/demo-chat') return {messages:[
    {role:'user',content:'Помоги придумать спокойный вечер без спешки.'},
    {role:'assistant',content:'Можно оставить всего три небольших дела.\n\n1. Прогуляться двадцать минут.\n2. Приготовить ужин под любимую музыку.\n3. Записать одну идею на завтра.\n\nОстальное время пусть останется свободным. Это демонстрационный ответ для просмотра темы.'},
  ]};
  if(path==='/api/audio/devices') return {microphone:false,speaker:false};
  if(path==='/api/dashboard/weather') return {state:'ready',temperature:4,code:3,location:{name:'Демо-город'},forecastTime:'11.11.2026 · 14:00',updatedAt:'14:35',forecast:[{time:'2026-11-11T12:00:00Z',temperature:4},{time:'2026-11-11T15:00:00Z',temperature:2},{time:'2026-11-11T18:00:00Z',temperature:1}]};
  if(path==='/api/dashboard/computer') return {state:'ready',profile:null,sample:{source:'Демо-компьютер',acquiredAt:'14:35',values:{cpuPct:42,cpuTemp:54,cpuGHz:3.6,fanRpm:1200,gpuPct:28,gpuTemp:46,gpuMemoryUsed:2*2**30,gpuMemoryTotal:8*2**30,gpuWatts:62,ramUsed:12.4*2**30,ramTotal:32*2**30,diskUsed:240*2**30,diskTotal:512*2**30,netRxBitsPerSecond:24.6e6,netTxBitsPerSecond:4.2e6}},history:series.map(cpuPct=>({cpuPct,gpuPct:cpuPct*.7,netRxBitsPerSecond:cpuPct*1e6}))};
  if(path==='/api/dashboard/markets') return {quotes,catalog:quotes,watchlist:quotes.map(q=>q.id),selected:quotes.find(q=>q.id===url.searchParams.get('instrument'))||quotes[0]};
  if(path==='/api/dashboard/calendar') return {storage:'session',events:[{id:'demo1',title:'Время для прогулки',date:'2026-11-11',time:'18:30'},{id:'demo2',title:'Новая идея',date:'2026-11-12',time:'10:00'}]};
  if(path==='/api/dashboard/photos') return {state:'ready',files:[{id:'demo-art',name:'Геометрический пейзаж.png'}]};
  return undefined;
}
