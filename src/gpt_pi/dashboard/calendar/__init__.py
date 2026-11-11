"""Session-owned event HTTP routes; no private persistence or cloud sync."""
from uuid import uuid4
from starlette.routing import Route
from starlette.responses import JSONResponse
from starlette.exceptions import HTTPException
from .model import validate_event

def routes(runtime,body):
 async def events(request):
  _,session=runtime.mutation(request,True) if request.method=='POST' else runtime.session(request,True)
  store=session.dashboard.setdefault('calendar',{})
  if request.method=='POST':
   data=await body(request)
   if 'id' in data and not isinstance(data['id'],str):raise HTTPException(400,'invalid_event')
   if data.get('action')=='delete' and set(data)=={'action','id'}:
    if data['id'] not in store:raise HTTPException(404,'not_found')
    del store[data['id']]
   else:
    try:event=validate_event(data)
    except (ValueError,TypeError):raise HTTPException(400,'invalid_event') from None
    identifier=data.get('id')
    if identifier and (not isinstance(identifier,str) or identifier not in store):raise HTTPException(404,'not_found')
    if not identifier and len(store)>=128:raise HTTPException(409,'event_limit')
    identifier=identifier or uuid4().hex
    store[identifier]={'id':identifier,**event}
  return JSONResponse({'events':sorted(store.values(),key=lambda e:(e['date'],e['time'],e['id'])),'storage':'session'})
 return [Route('/api/dashboard/calendar',events,methods=['GET','POST'])]
