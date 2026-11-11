import React,{useState} from 'react';
import {Button,Input,Field,Dialog,DialogSurface,DialogBody,DialogTitle,DialogContent,DialogActions} from '@fluentui/react-components';
import {ClockHero,CountdownCard,MonthCalendar,Panel} from '../assets/shared/components.jsx';
import {useResource,dashboardRequest} from '../shared/client.jsx';
import {calendarCells,moveMonth,calendarDays} from './model.mjs';
export function useCalendar(tab){return useResource('calendar',tab==='calendar',60000);}
export function CalendarScreen({sources,clock}) {
 const source=sources.calendar,events=source.value?.events||[];
 const [month,setMonth]=useState(clock.dateKey.slice(0,7)),[selected,setSelected]=useState(clock.dateKey),[edit,setEdit]=useState(null),[error,setError]=useState(''),[saving,setSaving]=useState(false),[target,setTarget]=useState('');
 const nextYear=Number(clock.dateKey.slice(0,4))+1;
 const countdown=target||`${nextYear}-01-01`;
 async function save(remove=false){setSaving(true);setError('');try{await dashboardRequest('calendar',remove?{action:'delete',id:edit.id}:edit);setEdit(null);source.refresh();}catch(e){setError(e.message==='session_expired'?'Войди в Ассистент, чтобы работать с личными событиями.':'Проверь название, дату и время события.');}finally{setSaving(false);}}
 return <><ClockHero time={clock.time} dateLabel={clock.date} artwork="/assets/holiday-tree.png" artworkAlt="Новогодняя ёлка" />
 <CountdownCard title={target&&target<clock.dateKey?'Дата прошла':target===clock.dateKey?'Сегодня':target?'До выбранной даты':'До Нового года'} countLabel={`${calendarDays(clock.dateKey,countdown)} дн.`} dateLabel={countdown}/>
 <Field label="Дата отсчёта"><Input type="date" value={target} onChange={(_,d)=>setTarget(d.value)} /></Field>
 <div className="dashboard-reference-layout"><MonthCalendar monthLabel={new Intl.DateTimeFormat('ru-RU',{month:'long',year:'numeric',timeZone:'UTC'}).format(new Date(month+'-01T12:00:00Z'))} cells={calendarCells(month,selected,clock.dateKey,events)} onPrevious={()=>setMonth(moveMonth(month,-1))} onNext={()=>setMonth(moveMonth(month,1))} onToday={()=>{setSelected(clock.dateKey);setMonth(clock.dateKey.slice(0,7));}} onSelect={cell=>setSelected(cell.dateTime)}/>
 <Panel title="Ближайшие события" actions={<Button onClick={()=>setEdit({title:'',date:selected,time:''})}>Добавить событие</Button>}>
 {source.error&&<p role="status">Для личных событий войди в Ассистент.</p>}
 {!events.length&&<p>Нет событий</p>}
 {events.filter(e=>e.date>=clock.dateKey).map(e=><div className="dashboard-agenda-row" key={e.id}><strong>{e.date} {e.time||'Весь день'}</strong><Button appearance="subtle" onClick={()=>setEdit({...e})}>{e.title}</Button></div>)}
 <details><summary>Прошедшие события</summary>{events.filter(e=>e.date<clock.dateKey).map(e=><Button key={e.id} appearance="subtle" onClick={()=>setEdit({...e})}>{e.date} · {e.title}</Button>)}</details>
 <p className="dashboard-small dashboard-secondary">События только в RAM текущего сеанса. Выход и перезапуск очищают их. Время — локальное, без часового смещения и уведомлений; смена часового пояса не переносит событие.</p>
 </Panel></div>
 <Dialog open={!!edit} onOpenChange={(_,d)=>{if(!d.open)setEdit(null);}}><DialogSurface><DialogBody><DialogTitle>Событие</DialogTitle><DialogContent>{edit&&<div className="dashboard-stack"><Field label="Название"><Input maxLength={120} value={edit.title} onChange={(_,d)=>setEdit({...edit,title:d.value})}/></Field><Field label="Дата"><Input type="date" value={edit.date} onChange={(_,d)=>setEdit({...edit,date:d.value})}/></Field><Field label="Время (необязательно)"><Input type="time" value={edit.time} onChange={(_,d)=>setEdit({...edit,time:d.value})}/></Field><p role="alert">{error}</p></div>}</DialogContent><DialogActions><Button disabled={saving} onClick={()=>setEdit(null)}>Отмена</Button>{edit?.id&&<Button disabled={saving} onClick={()=>save(true)}>Удалить</Button>}<Button appearance="primary" disabled={saving||!edit?.title.trim()||!edit?.date} onClick={()=>save()}>Сохранить</Button></DialogActions></DialogBody></DialogSurface></Dialog>
 </>;
}
