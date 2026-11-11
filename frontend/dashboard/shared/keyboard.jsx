import { useEffect, useState } from 'react';

// One poller while editing or while the native keyboard still occupies space.
export function useKeyboardInset() {
 const [height,setHeight]=useState(0);
 useEffect(()=>{
  let running=false,generation=0,timer,controller,pressed=false,pending,inset=0,releaseTimer;
  const editing=()=>{const el=document.activeElement;return el &&
   ((el.matches('textarea,input:not([type=checkbox]):not([type=radio]):not([type=button]):not([type=submit]):not([type=range]):not([type=file]):not([type=color]):not([type=hidden])')&&!el.readOnly&&!el.disabled)||el.isContentEditable);};
  const update=value=>{
   // A blur on pointer-down must not move a button before pointer-up/click.
   if(pressed){pending=value;return;}
   inset=value;setHeight(value);
  };
  const stop=()=>{running=false;generation++;clearTimeout(timer);controller?.abort();update(0);};
  const refresh=async mark=>{
   controller=new AbortController();
   try {
    const response=await fetch('/api/keyboard',{signal:controller.signal});
    if(response.ok){const data=await response.json();
     if(running&&mark===generation){
      const value=data.visible===true&&Number.isInteger(data.height)&&data.height>=0?Math.min(Math.round(data.height/(devicePixelRatio||1)),innerHeight):0;
      update(value);
      if(!editing()&&value===0)stop();
     }
    }
   } catch { /* Preserve space during a transient backend restart until blur. */ }
   if(running&&mark===generation)timer=setTimeout(()=>refresh(mark),400);
  };
  const sync=()=>{
   if(document.hidden||(!editing()&&inset===0)){stop();return;}
   if(!running){running=true;refresh(++generation);}
  };
  const focus=()=>queueMicrotask(sync);
  const down=()=>{pressed=true;};
  const up=()=>{pressed=false;clearTimeout(releaseTimer);releaseTimer=setTimeout(()=>{
   if(pending!==undefined){const value=pending;pending=undefined;update(value);}sync();
  },0);};
  document.addEventListener('focusin',focus);document.addEventListener('focusout',focus);document.addEventListener('visibilitychange',sync);
  document.addEventListener('pointerdown',down,true);document.addEventListener('pointerup',up,true);document.addEventListener('pointercancel',up,true);
  sync();
  return()=>{stop();clearTimeout(releaseTimer);document.removeEventListener('focusin',focus);document.removeEventListener('focusout',focus);document.removeEventListener('visibilitychange',sync);
   document.removeEventListener('pointerdown',down,true);document.removeEventListener('pointerup',up,true);document.removeEventListener('pointercancel',up,true);};
 },[]);
 useEffect(()=>{if(height>0)document.activeElement?.scrollIntoView?.({block:'nearest'});},[height]);
 return height;
}
