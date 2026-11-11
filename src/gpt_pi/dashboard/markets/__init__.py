from starlette.routing import Route
from starlette.responses import JSONResponse
from starlette.exceptions import HTTPException
from .service import Markets,CATALOG,PERIODS

def routes(runtime,body):
 service=runtime.markets=Markets()
 async def markets(request):
  _,session=runtime.mutation(request) if request.method=='POST' else runtime.session(request)
  watch=session.dashboard.setdefault('watchlist',list(CATALOG)[:6])
  if request.method=='POST':
   data=await body(request);items=data.get('watchlist')
   if set(data)!={'watchlist'} or not isinstance(items,list) or len(items)>12 or any(not isinstance(i,str) or i not in CATALOG for i in items) or len(set(items))!=len(items):raise HTTPException(400,'invalid_watchlist')
   session.dashboard['watchlist']=watch=items
  selected=request.query_params.get('instrument','kraken:XBTUSD');period=request.query_params.get('period','1D')
  if selected not in CATALOG or period not in PERIODS:raise HTTPException(400,'invalid_instrument')
  result=await service.snapshot(list(watch),selected,period)
  if not session.alive:raise HTTPException(401,'session_expired')
  return JSONResponse(result)
 return [Route('/api/dashboard/markets',markets,methods=['GET','POST'])]
