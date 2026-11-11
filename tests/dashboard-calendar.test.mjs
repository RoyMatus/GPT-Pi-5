import {test} from 'node:test';
import assert from 'node:assert/strict';
import {calendarCells,moveMonth,calendarDays} from '../frontend/dashboard/calendar/model.mjs';
test('Monday-first grid, leap year and fixed date semantics',()=>{
 const cells=calendarCells('2026-11','2026-11-10','2026-11-11',[{date:'2026-11-10'}]);
 assert.equal(cells.slice(0,6).every(x=>x===null),true);
 assert.equal(cells[15].day,10);assert.equal(cells[15].selected,true);assert.equal(cells[15].today,false);assert.equal(cells[15].hasEvent,true);
 assert.equal(calendarCells('2024-02','','').filter(Boolean).length,29);
 assert.equal(moveMonth('2026-12',1),'2027-01');assert.equal(moveMonth('2026-01',-1),'2025-12');
 assert.equal(calendarDays('2026-11-10','2027-01-01'),52);assert.equal(calendarDays('2026-03-28','2026-03-30'),2);
});
