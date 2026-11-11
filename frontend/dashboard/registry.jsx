import { ComputerScreen, useComputer } from './computer/screen.jsx';
import { MarketsScreen, useMarkets } from './markets/screen.jsx';
import { CalendarScreen, useCalendar } from './calendar/screen.jsx';
import { PhotosScreen, usePhotos } from './photos/screen.jsx';
/** Integration-owned registry: screen and source hooks have one stable order. */
export const screenIds=Object.freeze(['overview','computer','markets','calendar','photos','assistant']);
export function createRegistry(entries) {
 const registry=new Map();
 for(const [id,component] of Object.entries(entries)) {
  if(!screenIds.includes(id)||typeof component!=='function')throw new TypeError('Invalid screen registration');
  registry.set(id,component);
 }
 return id=>registry.get(id);
}
export const features=Object.freeze({photos:{screen:PhotosScreen,useSource:usePhotos},computer:{screen:ComputerScreen,useSource:useComputer},markets:{screen:MarketsScreen,useSource:useMarkets},calendar:{screen:CalendarScreen,useSource:useCalendar}});
export function useSources(tab) {
 return Object.fromEntries(Object.entries(features).map(([id,entry])=>[id,entry.useSource(tab)]));
}
