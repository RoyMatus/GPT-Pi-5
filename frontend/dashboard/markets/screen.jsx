import React,{useId,useState} from 'react';
import {Button,Select,Field} from '@fluentui/react-components';
import {Panel,MetricCard,Sparkline} from '../assets/shared/components.jsx';
import {useResource,dashboardRequest} from '../shared/client.jsx';
export function useMarkets(tab){const[selected,setSelected]=useState('kraken:XBTUSD'),[period,setPeriod]=useState('1D');return {...useResource(`markets?instrument=${encodeURIComponent(selected)}&period=${period}`,tab==='markets'||tab==='overview',60000),selected,setSelected,period,setPeriod};}
export const money=q=>q?.value==null?'—':new Intl.NumberFormat('ru-RU',{maximumFractionDigits:q.category==='fx'?4:2}).format(q.value)+(q.currency==='USD'?' $':q.currency==='RUB'?' ₽':q.currency==='points'?' п.':' '+q.currency);
export function QuoteCard({quote:q,onChoose,large=false}){if(!q)return <Panel><p role="status">Загрузка котировки…</p></Panel>;return <MetricCard label={q.label} value={money(q)} detail={q.change==null?'Изменение недоступно':`${q.change>0?'+':''}${q.change.toFixed(2)}%`}><Sparkline values={q.history.map(p=>p.value)} label={`${q.label}: ${q.period}`} large={large} tone={q.change<0?'negative':'positive'}/><p className="dashboard-small dashboard-secondary">{q.provider} · {q.state==='ready'?'Получено':q.state==='stale'?'Устаревшие данные':q.state==='unsupported'?'Не поддерживается':'Недоступно'}<br/>{q.detail}<br/>{q.quoteTime||'Нет времени котировки'}</p>{onChoose&&<Button appearance="subtle" onClick={onChoose}>Открыть {q.label}</Button>}</MetricCard>;}
export function MarketSummary({source,onNavigate}){const quotes=source.value?.quotes||[];return <Panel title="Рынки"><div className="dashboard-grid">{quotes.slice(0,4).map(q=><QuoteCard key={q.id} quote={q} onChoose={()=>{source.setSelected(q.id);onNavigate('markets');}}/>)}</div>{!quotes.length&&<p role="status">{source.error?'Источник недоступен':'Загрузка рынков…'}</p>}</Panel>;}
function WatchlistRow({quote:q,onChoose,selected}) {
 const descriptionId=useId();
 const state=q.state==='ready'?'Получено':q.state==='stale'?'Устаревшие данные':q.state==='unsupported'?'Не поддерживается':'Недоступно';
 return <Button appearance="transparent" className="dashboard-watchlist-row" aria-label={`Открыть ${q.label}`} aria-describedby={`${descriptionId}-price ${descriptionId}-state`} aria-pressed={selected} onClick={onChoose}>
  <span className="dashboard-watchlist-name"><strong>{q.label}</strong><small id={`${descriptionId}-state`}>{state}</small></span>
  <Sparkline values={q.history.map(p=>p.value)} label={`${q.label}: ${q.period}`} tone={q.change<0?'negative':'positive'}/>
  <span id={`${descriptionId}-price`} className="dashboard-watchlist-price"><strong>{money(q)}</strong><small className={q.change<0?'dashboard-negative':'dashboard-positive'}>{q.change==null?'—':`${q.change>0?'+':''}${q.change.toFixed(2)}%`}</small></span>
 </Button>;
}
export function MarketsScreen({sources}) {
 const source=sources.markets,[filter,setFilter]=useState('all'),[add,setAdd]=useState(''),[notice,setNotice]=useState('');
 const data=source.value,watch=data?.watchlist||[],catalog=data?.catalog||[];
 const quotes=data?.quotes||[];
 async function update(items){try{await dashboardRequest('markets',{watchlist:items});source.refresh();setNotice('');}catch{setNotice('Не удалось обновить избранное.');}}
 return <div className="dashboard-reference-layout"><div className="dashboard-reference-section"><QuoteCard quote={data?.selected} large/>
 <div className="dashboard-row">{['1D','1W','1M','1Y'].map(p=><Button key={p} appearance={source.period===p?'primary':'secondary'} onClick={()=>source.setPeriod(p)}>{p}</Button>)}</div><p className="dashboard-small dashboard-secondary">Изменение от первой до последней доступной свечи выбранного периода. У валют — официальный курс ЦБ за единицу. Не торговый терминал.</p></div>
 <div className="dashboard-reference-section"><Panel title="Избранное"><Field label="Категория"><Select value={filter} onChange={(_,d)=>setFilter(d.value)}>{[['all','Все'],['crypto','Криптовалюты'],['stock','Акции'],['index','Индексы'],['fx','Валюты'],['commodity','Сырьё']].map(([id,label])=><option key={id} value={id}>{label}</option>)}</Select></Field>
 <div className="dashboard-watchlist">{quotes.filter(q=>filter==='all'||q.category===filter).map(q=><WatchlistRow key={q.id} quote={q} selected={source.selected===q.id} onChoose={()=>source.setSelected(q.id)}/>)}</div>
 {!watch.length&&<p>Избранное пусто. Открой «Управлять избранным», чтобы добавить инструмент.</p>}
 <details className="dashboard-disclosure"><summary>Управлять избранным</summary><div className="dashboard-disclosure-content">
  {watch.map((id,index)=>{const label=catalog.find(item=>item.id===id)?.label||id;return <div key={id} className="dashboard-watchlist-manage-row"><span>{label}</span><Button disabled={index===0} onClick={()=>{const next=[...watch];[next[index-1],next[index]]=[next[index],next[index-1]];update(next);}}>Выше</Button><Button onClick={()=>update(watch.filter(item=>item!==id))}>Убрать {label}</Button></div>;})}
  <Field label="Добавить инструмент"><Select value={add} onChange={(_,d)=>setAdd(d.value)}><option value="">Выбери инструмент</option>{catalog.filter(i=>!watch.includes(i.id)).map(i=><option key={i.id} value={i.id}>{i.label}</option>)}</Select></Field><Button disabled={!add||watch.includes(add)} onClick={()=>update([...watch,add])}>Добавить</Button>
  <p className="dashboard-small dashboard-secondary">Избранное только в текущем сеансе.</p>
 </div></details>
 <p role="status">{notice||source.error}</p>
 <details className="dashboard-disclosure"><summary>Источники и время котировок</summary><div className="dashboard-disclosure-content">
  {quotes.map(q=><p key={q.id} className="dashboard-small dashboard-secondary">{q.label} · {q.provider} · {q.quoteTime||'Нет времени котировки'}<br/>{q.detail}</p>)}
  <p className="dashboard-small dashboard-secondary">Поставщики: <a href="https://docs.kraken.com/api/" target="_blank" rel="noreferrer">Kraken</a>, <a href="https://www.moex.com/a2920" target="_blank" rel="noreferrer">MOEX ISS</a>, <a href="https://www.cbr.ru/development/sxml/" target="_blank" rel="noreferrer">Банк России</a>. MOEX — задержанные данные. Источник нефти и металлов не подключён; spot/futures не подменяются.</p>
 </div></details></Panel></div></div>;
}
