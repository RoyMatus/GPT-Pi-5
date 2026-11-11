import React, { useEffect, useRef, useState } from 'react';
import { Button, Switch, webLightTheme, FluentProvider } from '@fluentui/react-components';
import { DashboardFrame, dashboardTheme, Panel, ClockHero } from '../assets/shared/components.jsx';
import { dashboardTabs } from '../assets/shared/icons.jsx';
import { ScreenLifecycle } from '../shared/contracts.mjs';
import { useClock } from '../shared/clock.jsx';
import './shell.css';
const unavailable={overview:'Погода и сводки ещё не подключены.',computer:'Компьютер не настроен. Показатели недоступны.',markets:'Источник котировок ещё не подключён.',calendar:'События и календарь ещё не подключены.',photos:'Папка фотографий не разрешена.',assistant:'Существующий ассистент доступен отдельно до переноса в панель.'};
export function DashboardShell() {
 const [tab,setTab]=useState('overview');
 const [light,setLight]=useState(()=>localStorage.getItem('gpt-pi-theme')!=='dark');
 const [settings,setSettings]=useState(false);
 const lifecycle=useRef(new ScreenLifecycle());
 const clock=useClock();
 useEffect(()=>{ lifecycle.current.activate(tab); return ()=>lifecycle.current.dispose(); },[tab]);
 const title=dashboardTabs.find(t=>t.id===tab).label;
 return <FluentProvider theme={light?webLightTheme:dashboardTheme} className={`dashboard dashboard-viewport ${light?'dashboard-light':''}`}>
  <DashboardFrame title={title} activeTab={tab} onNavigate={setTab} onSettings={()=>setSettings(v=>!v)} connectionLabel="ПК не настроен">
   {settings && <Panel title="Настройки панели"><Switch label="Светлая тема" checked={light} onChange={(_,d)=>{setLight(d.checked);localStorage.setItem('gpt-pi-theme',d.checked?'light':'dark');}} /><p>Часовой пояс: {clock.timeZone}. Используется часовой пояс системы.</p></Panel>}
   {(tab==='overview'||tab==='calendar') && <ClockHero time={clock.time} dateLabel={clock.date} />}
   <Panel title={title}><p role="status">{unavailable[tab]}</p><p className="dashboard-secondary">Оболочка панели · интеграции в разработке</p>
    <Button as="a" href="/" appearance="primary">Открыть существующий ассистент</Button>
   </Panel>
  </DashboardFrame>
 </FluentProvider>;
}

