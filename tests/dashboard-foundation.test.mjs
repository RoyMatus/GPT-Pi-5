import { test } from 'node:test';
import assert from 'node:assert/strict';
import { ScreenLifecycle, SourceStore, clockSnapshot } from '../frontend/dashboard/shared/contracts.mjs';
test('switch aborts outgoing tasks and rejects late source results', () => {
 const lifecycle = new ScreenLifecycle();
 const first = lifecycle.activate('computer');
 lifecycle.activate('photos');
 assert.equal(first.signal.aborted, true);
 assert.equal(first.current(), false);
 const store = new SourceStore();
 const generation = store.select('pc-a');
 store.select('pc-b');
 assert.equal(store.publish(generation, { value: 70 }), false);
 assert.equal(store.snapshot().value, null);
});
test('multiple consumers share one producer, last departure stops it', () => {
 let starts=0, stops=0;
 const store = new SourceStore(() => { starts++; return () => stops++; });
 const a=store.subscribe(()=>{}), b=store.subscribe(()=>{});
 assert.equal(starts,1); a(); assert.equal(stops,0); b(); b(); assert.equal(stops,1);
});
test('clock follows timezone and real midnight without accumulating timer drift', () => {
 const instant = new Date('2026-12-31T22:30:00Z');
 assert.equal(clockSnapshot(instant,'Europe/Moscow').dateKey,'2027-01-01');
 assert.equal(clockSnapshot(instant,'UTC').dateKey,'2026-12-31');
 assert.throws(()=>clockSnapshot(instant,'Invalid/Zone'), RangeError);
});
