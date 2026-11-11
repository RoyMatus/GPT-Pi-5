export function calendarCells(month,selected,today,events=[]) {
 const [year,m]=month.split('-').map(Number), first=new Date(Date.UTC(year,m-1,1));
 const offset=(first.getUTCDay()+6)%7,days=new Date(Date.UTC(year,m,0)).getUTCDate();
 return [...Array(offset).fill(null),...Array.from({length:days},(_,i)=>{
  const dateTime=`${month}-${String(i+1).padStart(2,'0')}`;
  return {key:dateTime,dateTime,day:i+1,selected:dateTime===selected,today:dateTime===today,hasEvent:events.some(e=>e.date===dateTime)};
 })];
}
export function moveMonth(month,delta){const[y,m]=month.split('-').map(Number);return new Date(Date.UTC(y,m-1+delta,1)).toISOString().slice(0,7);}
export function calendarDays(today,target){return Math.max(0,Math.round((Date.parse(target+'T00:00:00Z')-Date.parse(today+'T00:00:00Z'))/86400000));}
