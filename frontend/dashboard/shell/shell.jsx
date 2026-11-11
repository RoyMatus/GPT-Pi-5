import React, { useEffect, useState } from 'react';
import { Button, Switch, webLightTheme, FluentProvider } from '@fluentui/react-components';
import { DashboardFrame, dashboardTheme, Panel, ClockHero } from '../assets/shared/components.jsx';
import { dashboardTabs } from '../assets/shared/icons.jsx';
import { useClock } from '../shared/clock.jsx';
import './shell.css';
import { sourceStates } from '../computer/screen.jsx';
import { features, useSources } from '../registry.jsx';
import '../assistant/assistant.css';
const unavailable={overview:'Источники погоды и сводок ещё не настроены.',computer:'Компьютер не настроен.',markets:'Источник котировок ещё не настроен.',calendar:'Событий нет.',photos:'Папка фотографий не разрешена.'};
export function DashboardShell({ Assistant }) {
 const [tab,setTab]=useState(()=>new URLSearchParams(location.search).has('dashboard')?'overview':'assistant');
 const [light,setLight]=useState(()=>localStorage.getItem('gpt-pi-theme')!=='dark');
 const [settings,setSettings]=useState(false);
 const [fullscreen,setFullscreen]=useState(false);
 const navigate=next=>{setFullscreen(false);setTab(next);};
 const clock=useClock();
 const sources=useSources(tab);
 const Screen=features[tab]?.screen;
 useEffect(()=>{const logout=()=>setTab('assistant');window.addEventListener('gpt-pi-logout',logout);return()=>window.removeEventListener('gpt-pi-logout',logout);},[]);
 const title=dashboardTabs.find(t=>t.id===tab).label;
 return <FluentProvider theme={light?webLightTheme:dashboardTheme} className={`dashboard dashboard-viewport ${light?'dashboard-light':''}`}>
  <DashboardFrame fullscreen={fullscreen} title={title} activeTab={tab} onNavigate={navigate} onSettings={tab==='assistant'?undefined:()=>setSettings(v=>!v)} connected={sources.computer?.value?.state==='ready'} connectionLabel={sourceStates[sources.computer?.value?.state]||'ПК не настроен'}>
   {settings && <Panel title="Настройки панели"><Switch label="Светлая тема" checked={light} onChange={(_,d)=>{setLight(d.checked);localStorage.setItem('gpt-pi-theme',d.checked?'light':'dark');}} /><p>Часовой пояс: {clock.timeZone}</p></Panel>}
   <div className="dashboard-assistant-slot" hidden={tab!=='assistant'}><Assistant active={tab==='assistant'} themeDark={!light} onThemeChange={setLight} /></div>
   {tab!=='assistant' && (Screen ? <Screen sources={sources} onNavigate={navigate} clock={clock} setFullscreen={setFullscreen} /> : <>{(tab==='overview'||tab==='calendar') && <ClockHero time={clock.time} dateLabel={clock.date} />}<Panel title={title}><p role="status">{unavailable[tab]}</p></Panel></>)}
  </DashboardFrame>
 </FluentProvider>;
}
