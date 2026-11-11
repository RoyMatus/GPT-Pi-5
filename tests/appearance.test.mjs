import test from 'node:test';
import assert from 'node:assert/strict';
import {schemes,resolveAppearance,readAppearance,saveAppearance,appearanceVariables} from '../frontend/themes.mjs';
function contrast(a,b) {
  const lum=hex=>hex.slice(1).match(/../g).map(v=>parseInt(v,16)/255).map(v=>v<=.04045?v/12.92:((v+.055)/1.055)**2.4).reduce((s,v,i)=>s+v*[.2126,.7152,.0722][i],0);
  return (Math.max(lum(a),lum(b))+.05)/(Math.min(lum(a),lum(b))+.05);
}
test('legacy light/dark preferences survive migration and invalid scheme IDs',()=>{
  const data=new Map([['gpt-pi-theme','dark']]);const storage={getItem:k=>data.get(k),setItem:(k,v)=>data.set(k,v)};
  assert.equal(readAppearance(storage).id,'fluent_dark');assert.equal(readAppearance(storage).light,false);
  data.set('gpt-pi-scheme','unknown');assert.equal(readAppearance(storage).light,false);
  saveAppearance(storage,resolveAppearance('solarized_light'));assert.equal(readAppearance(storage).id,'solarized_light');
  assert.equal(data.get('gpt-pi-theme'),'dark','A new scheme must preserve the previous Fluent brightness');
});
test('denied storage does not prevent applying a theme',()=>{
  const storage={getItem(){throw Error('denied');},setItem(){throw Error('denied');}};
  assert.equal(readAppearance(storage).id,'fluent_light');assert.equal(saveAppearance(storage,resolveAppearance('nord')),false);
});
test('small recording/error status is legible on each themed reading surface',()=>{
  for(const scheme of schemes) {
    const theme=resolveAppearance(scheme.id),variables=appearanceVariables(theme);
    for(const surface of [theme.background,theme.panel,variables['--scheme-selected']])
      assert(contrast(variables['--scheme-negative'],surface)>=4.5,`${scheme.id}: recording status contrast below 4.5`);
  }
});
test('fifteen schemes include independent Fluent modes and monochrome green',()=>{
  assert.equal(schemes.length,15);
  for(const id of ['fluent_light','fluent_dark','green_phosphor']) assert.equal(resolveAppearance(id).id,id);
  assert.equal(resolveAppearance('fluent','dark').id,'fluent_dark');
  assert.equal(resolveAppearance('fluent','light').id,'fluent_light');
  const green=resolveAppearance('green_phosphor');
  assert.equal(green.light,false);assert.equal(green.positive,green.control);
  assert.equal(green.roles.destructive,green.control);
});
