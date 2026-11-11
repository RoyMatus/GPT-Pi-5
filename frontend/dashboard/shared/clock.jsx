import { useEffect, useState } from 'react';
import { clockSnapshot } from './contracts.mjs';
// One clock subscription service. Re-read wall time on wake; never increment a counter.
const listeners = new Set();
let timer;
const update=()=>{ for(const listener of listeners) listener(); };
export function useClock(timeZone) {
 const [clock,setClock]=useState(()=>clockSnapshot(new Date(),timeZone));
 useEffect(()=>{
  const listener=()=>setClock(clockSnapshot(new Date(),timeZone));
  listeners.add(listener); listener();
  if(listeners.size===1) { timer=setInterval(update,1000); window.addEventListener('pageshow',update); document.addEventListener('visibilitychange',update); }
  return ()=>{ listeners.delete(listener); if(!listeners.size) { clearInterval(timer); window.removeEventListener('pageshow',update); document.removeEventListener('visibilitychange',update); } };
 },[timeZone]);
 return clock;
}
