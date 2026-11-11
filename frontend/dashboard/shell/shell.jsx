import React, { useEffect, useState } from 'react';
import { FluentProvider } from '@fluentui/react-components';
import { DashboardFrame, Panel, ClockHero } from '../assets/shared/components.jsx';
import { dashboardTabs } from '../assets/shared/icons.jsx';
import { useClock } from '../shared/clock.jsx';
import { useKeyboardInset } from '../shared/keyboard.jsx';
import './shell.css';
import { sourceStates } from '../computer/screen.jsx';
import { features, useSources } from '../registry.jsx';
import '../assistant/assistant.css';
import { useAppearance, fluentAppearance, ThemePicker } from '../../appearance.jsx';
import { appearanceVariables } from '../../themes.mjs';
const unavailable={overview:'Источники погоды и сводок ещё не настроены.',computer:'Компьютер не настроен.',markets:'Источник котировок ещё не настроен.',calendar:'Событий нет.',photos:'Папка фотографий не разрешена.'};
export function DashboardShell({ Assistant }) {
 const [tab,setTab]=useState(()=>new URLSearchParams(location.search).has('dashboard')?'overview':'assistant');
 const {appearance,setAppearance,saved}=useAppearance();
 const [settings,setSettings]=useState(false);
 const [fullscreen,setFullscreen]=useState(false);
 const navigate=next=>{setFullscreen(false);setTab(next);};
 const clock=useClock();
 const keyboardInset=useKeyboardInset();
 const sources=useSources(tab);
 const Screen=features[tab]?.screen;
 useEffect(()=>{const logout=()=>setTab('assistant');window.addEventListener('gpt-pi-logout',logout);return()=>window.removeEventListener('gpt-pi-logout',logout);},[]);
 const title=dashboardTabs.find(t=>t.id===tab).label;
 return <FluentProvider theme={fluentAppearance(appearance)} data-theme={appearance.id} style={{...appearanceVariables(appearance),height:`calc(100dvh - ${keyboardInset}px)`}} className={`dashboard dashboard-viewport ${appearance.light?'dashboard-light':''}`}>
  <DashboardFrame fullscreen={fullscreen} title={title} activeTab={tab} onNavigate={navigate} onSettings={tab==='assistant'?undefined:()=>setSettings(v=>!v)} connected={sources.computer?.value?.state==='ready'} connectionLabel={sourceStates[sources.computer?.value?.state]||'ПК не настроен'}>
   {settings && <Panel title="Настройки панели"><ThemePicker appearance={appearance} onChange={setAppearance} saved={saved} /><p>Часовой пояс: {clock.timeZone}</p></Panel>}
   <div className="dashboard-assistant-slot" hidden={tab!=='assistant'}><Assistant active={tab==='assistant'} appearance={appearance} onAppearanceChange={setAppearance} appearanceSaved={saved} /></div>
   {tab!=='assistant' && (Screen ? <Screen sources={sources} onNavigate={navigate} clock={clock} setFullscreen={setFullscreen} /> : <>{(tab==='overview'||tab==='calendar') && <ClockHero time={clock.time} dateLabel={clock.date} />}<Panel title={title}><p role="status">{unavailable[tab]}</p></Panel></>)}
  </DashboardFrame>
 </FluentProvider>;
}
