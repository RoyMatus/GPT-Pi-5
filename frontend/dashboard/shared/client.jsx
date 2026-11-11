import { useCallback, useEffect, useRef, useState } from 'react';
let sessionRead;
export function readSession(){
 if(!sessionRead)sessionRead=fetch('/api/session',{credentials:'same-origin'}).finally(()=>{sessionRead=undefined;});
 return sessionRead.then(response=>response.clone());
}
export async function dashboardRequest(path, data, signal) {
 const options={credentials:'same-origin',signal};
 const auth=await readSession();
 if(signal?.aborted)throw new DOMException('Aborted','AbortError');
 if(data!==undefined) {
  const session=await auth.json();
  Object.assign(options,{method:'POST',headers:{'Content-Type':'application/json','X-CSRF-Token':session.csrf},body:JSON.stringify(data)});
 }
 const response=await fetch('/api/dashboard/'+path,options);
 const result=await response.json();
 if(!response.ok) throw new Error(result.error||'connection');
 return result;
}
export function useResource(path,enabled,interval=60000) {
 const [value,setValue]=useState(null),[error,setError]=useState(''),[revision,setRevision]=useState(0);
 const generation=useRef(0);
 const previousPath=useRef(path);
 const [visible,setVisible]=useState(()=>!document.hidden);
 useEffect(()=>{const visibility=()=>setVisible(!document.hidden);document.addEventListener("visibilitychange",visibility);return()=>document.removeEventListener("visibilitychange",visibility);},[]);
 const refresh=useCallback(()=>setRevision(v=>v+1),[]);
 useEffect(()=>{
  if(previousPath.current!==path){previousPath.current=path;setValue(null);setError('');}
  if(!enabled||!visible)return;
  const controller=new AbortController();const mark=++generation.current;let timer;
  async function update(){
   try { const next=await dashboardRequest(path,undefined,controller.signal);if(!controller.signal.aborted && mark===generation.current){setValue(next);setError('');} }
   catch(e){if(!controller.signal.aborted && mark===generation.current)setError(e.message);}
   if(!controller.signal.aborted && mark===generation.current)timer=setTimeout(update,interval);
  }
  update();return()=>{controller.abort();clearTimeout(timer);};
 },[path,enabled,visible,interval,revision]);
 useEffect(()=>{const clear=()=>{generation.current++;setValue(null);setError('');};window.addEventListener('gpt-pi-logout',clear);return()=>window.removeEventListener('gpt-pi-logout',clear);},[]);
 return {value,error,refresh};
}
