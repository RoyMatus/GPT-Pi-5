import React,{useState} from 'react';
import {Button,Input,Field,Select,Checkbox} from '@fluentui/react-components';
import {Panel,MetricCard,Sparkline,ProgressMeter} from '../assets/shared/components.jsx';
import {dashboardIcons as Icon} from '../assets/shared/icons.jsx';
import {useResource,dashboardRequest} from '../shared/client.jsx';
export const sourceStates={not_configured:'ПК не настроен',configured:'Ожидание данных',disabled:'Подключение отключено',ready:'ПК подключён',verification_required:'Нужно проверить ключ сервера',host_key_changed:'Ключ сервера изменился — подключение заблокировано',authentication_failed:'Сервер отклонил ключ доступа',unreachable:'ПК недоступен по SSH',timeout:'Время подключения истекло',collector_failed:'Сборщик недоступен: проверь ОС и разрешения',invalid_sample:'Сервер вернул некорректные данные'};
export function useComputer(tab){return useResource('computer',tab==='computer'||tab==='overview',3000);}
const fmt=(n,d=1)=>Number.isFinite(n)?new Intl.NumberFormat('ru-RU',{maximumFractionDigits:d}).format(n):'—';
const pct=n=>n==null?'—':fmt(n)+'%';
const bytes=(used,total)=>used==null||total==null?'—':`${fmt(used/1073741824)} / ${fmt(total/1073741824)} ГиБ`;
const percent=(used,total)=>total>0&&used!=null?100*used/total:null;
export function ComputerSummary({source,onNavigate,compact=false}){
 const data=source.value,m=data?.sample?.values||{},history=data?.history||[];
 return <Panel title={compact?'Мой компьютер':'Показатели компьютера'} icon={Icon.computer} actions={compact&&<Button onClick={()=>onNavigate('computer')}>Подробнее</Button>}>
 <p role="status" className="dashboard-secondary">{source.error==='session_expired'?'Войди в Ассистент для доступа к личному ПК':sourceStates[data?.state]||'Получение состояния…'}{data?.sample?.stale?' · предыдущие данные устарели':''}</p>
 <div className="dashboard-grid"><MetricCard label="CPU" value={pct(m.cpuPct)} detail={m.cpuTemp==null?'Температура недоступна':fmt(m.cpuTemp)+' °C'} icon={Icon.cpu}><Sparkline values={history.map(v=>v.cpuPct)} min={0} max={100} label="Загрузка CPU" large={!compact}/>{!compact&&<p>Частота {fmt(m.cpuGHz)} ГГц · вентилятор {fmt(m.fanRpm,0)} об/мин</p>}</MetricCard>
 <MetricCard label="GPU" value={pct(m.gpuPct)} detail={m.gpuTemp==null?'Температура недоступна':fmt(m.gpuTemp)+' °C'} icon={Icon.gpu}><Sparkline values={history.map(v=>v.gpuPct)} min={0} max={100} label="Загрузка GPU" tone="cyan" large={!compact}/>{!compact&&<p>Видеопамять {bytes(m.gpuMemoryUsed,m.gpuMemoryTotal)} · {fmt(m.gpuWatts)} Вт</p>}</MetricCard>
 <MetricCard label="Память" value={bytes(m.ramUsed,m.ramTotal)} detail={pct(percent(m.ramUsed,m.ramTotal))} icon={Icon.memory}><ProgressMeter value={percent(m.ramUsed,m.ramTotal)} label="Использование памяти"/></MetricCard>
 <MetricCard label="Сеть" value={`↓ ${m.netRxBitsPerSecond==null?'—':fmt(m.netRxBitsPerSecond/1000000)} Мбит/с`} detail={`↑ ${m.netTxBitsPerSecond==null?'—':fmt(m.netTxBitsPerSecond/1000000)} Мбит/с`} icon={Icon.network}><Sparkline values={history.map(v=>v.netRxBitsPerSecond)} label="Входящий сетевой трафик" tone="cyan"/></MetricCard></div>
 <MetricCard label="Системный накопитель" value={bytes(m.diskUsed,m.diskTotal)} icon={Icon.disk}><ProgressMeter value={percent(m.diskUsed,m.diskTotal)} label="Использование диска"/></MetricCard>
 {data?.sample?.acquiredAt&&<p className="dashboard-small dashboard-secondary">Источник: {data.sample.source} · получено {data.sample.acquiredAt} · история до 60 точек</p>}
 </Panel>;
}
export function ComputerScreen({sources,onNavigate}){
 const source=sources.computer,[setup,setSetup]=useState(false),[notice,setNotice]=useState(''),[pending,setPending]=useState(false);
 const [form,setForm]=useState({host:'',port:22,user:'',photoUser:'',platform:'linux',fingerprint:'',label:'Мой компьютер',verified:false});
 const set=(key,value)=>setForm(v=>({...v,[key]:value}));
 async function action(data){setPending(true);try{await dashboardRequest('computer',data);source.refresh();setNotice('Настройки применены.');if(data.action==='configure')setSetup(false);}catch{setNotice('Не удалось применить настройки. Проверь поля, вход и доступность хранилища.');}finally{setPending(false);}}
 const profile=source.value?.profile;
 return <><ComputerSummary source={source} onNavigate={onNavigate}/><Panel title="SSH-подключение"><div className="dashboard-row"><Button onClick={()=>{if(profile)setForm({...profile,verified:false});setSetup(v=>!v);}}>Настроить компьютер</Button><Button onClick={()=>source.refresh()}>Обновить</Button>{profile&&<><Button disabled={pending} onClick={()=>action({action:'disable'})}>Отключить</Button><Button disabled={pending} onClick={()=>action({action:'remove'})}>Удалить подключение</Button></>}</div>
 {source.error==='session_expired'&&<Button onClick={()=>onNavigate('assistant')}>Войти в Ассистент</Button>}
 {setup&&<div className="dashboard-stack"><Field label="Имя компьютера"><Input value={form.label} onChange={(_,d)=>set('label',d.value)}/></Field><Field label="Адрес SSH"><Input value={form.host} onChange={(_,d)=>set('host',d.value)}/></Field><Field label="Порт SSH"><Input type="number" min={1} max={65535} value={String(form.port)} onChange={(_,d)=>set('port',Number(d.value))}/></Field><Field label="Пользователь телеметрии"><Input value={form.user} onChange={(_,d)=>set('user',d.value)}/></Field><Field label="Пользователь фото (отдельная учётная запись рекомендуется)"><Input value={form.photoUser} onChange={(_,d)=>set('photoUser',d.value)}/></Field><Field label="ОС источника"><Select value={form.platform} onChange={(_,d)=>set('platform',d.value)}><option value="linux">Linux · Python 3</option><option value="windows">Windows · PowerShell/CIM</option></Select></Field><Field label="Проверенный SHA256-отпечаток SSH-сервера"><Input value={form.fingerprint} onChange={(_,d)=>set('fingerprint',d.value)}/></Field><p>Сверь отпечаток с выводом ssh-keygen -lf файла публичного host-ключа непосредственно на ПК. Не копируй приватный ключ. Изменение ключа блокирует подключение.</p><Checkbox checked={form.verified} label="Я сверил отпечаток по доверенному каналу" onChange={(_,d)=>set('verified',!!d.checked)}/><Button appearance="primary" disabled={pending||!form.verified} onClick={()=>{const{enabled,...data}=form;action({action:'configure',...data});}}>Сохранить подключение</Button></div>}
 <p role="status">{notice}</p>
 {profile&&<><p>Добавь этот публичный ключ в разрешённые ключи отдельной учётной записи телеметрии на ПК:</p><textarea aria-label="Публичный ключ телеметрии" readOnly value={source.value?.publicKey||''} style={{width:'100%',minHeight:90}}/><p>Ключ для отдельной учётной записи SFTP:</p><textarea aria-label="Публичный ключ фото" readOnly value={source.value?.photoPublicKey||''} style={{width:'100%',minHeight:90}}/><Button disabled={pending} onClick={()=>{if(window.confirm('Ротация отключит существующие ключи на устройстве. Новые публичные ключи нужно добавить на ПК. Продолжить?'))action({action:'rotate'});}}>Заменить ключи</Button></>}
 <p className="dashboard-small dashboard-secondary">Без агента на ПК. Нужен настроенный OpenSSH-сервер. Приватные ключи создаются и остаются на backend; пароль ПК приложение не принимает. Удаление здесь не удаляет публичный ключ на ПК. Доступ к телеметрии не разрешает папку фото. Облачной модели SSH недоступен.</p>
 </Panel></>;
}
