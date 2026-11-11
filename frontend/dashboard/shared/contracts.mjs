/** A screen's resources end before the next screen activates. */
export class ScreenLifecycle {
 #controller; #generation = 0;
 activate(id) {
  this.#controller?.abort();
  const controller = this.#controller = new AbortController();
  const generation = ++this.#generation;
  return Object.freeze({ id, generation, signal: controller.signal,
   current: () => generation === this.#generation && !controller.signal.aborted });
 }
 dispose() { this.#controller?.abort(); this.#generation++; }
}
/** One producer per source store, shared by Overview and its detail screen. */
export class SourceStore {
 #generation=0; #listeners=new Set(); #stop; #start;
 #sample=Object.freeze({source:null,value:null,state:'not_configured',generation:0});
 constructor(start = () => () => {}) { this.#start=start; }
 snapshot() { return this.#sample; }
 select(source) {
  this.#generation++;
  this.#sample=Object.freeze({source,value:null,state:source?'loading':'not_configured',generation:this.#generation});
  this.#notify(); return this.#generation;
 }
 publish(generation, sample) {
  if(generation!==this.#generation) return false;
  this.#sample=Object.freeze({...sample,source:this.#sample.source,generation});
  this.#notify(); return true;
 }
 #notify() { for(const listener of this.#listeners) listener(this.#sample); }
 subscribe(listener) {
  // Each subscription has its own identity, even for the same callback.
  const notify = value => listener(value);
  this.#listeners.add(notify);
  if(this.#listeners.size===1) this.#stop=this.#start(this);
  let active=true;
  return () => { if(!active) return; active=false; this.#listeners.delete(notify);
   if(!this.#listeners.size) { this.#stop?.(); this.#stop=undefined; this.#generation++; }
  };
 }
}
export function clockSnapshot(now = new Date(), timeZone = Intl.DateTimeFormat().resolvedOptions().timeZone, locale='ru-RU') {
 const dateParts = new Intl.DateTimeFormat('en-CA',{timeZone,year:'numeric',month:'2-digit',day:'2-digit'}).formatToParts(now);
 const part = type => dateParts.find(p=>p.type===type).value;
 return Object.freeze({ instant:now.toISOString(), timeZone,
  dateKey:`${part('year')}-${part('month')}-${part('day')}`,
  time:new Intl.DateTimeFormat(locale,{timeZone,hour:'2-digit',minute:'2-digit'}).format(now),
  date:new Intl.DateTimeFormat(locale,{timeZone,dateStyle:'full'}).format(now) });
}
