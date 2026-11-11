from starlette.routing import Route
from starlette.responses import JSONResponse
from starlette.exceptions import HTTPException
import httpx,time
from .weather import Weather,DEFAULT_LOCATION,validate_location

def routes(runtime,body):
 service=runtime.weather=Weather()
 async def weather(request):
  _,session=runtime.mutation(request) if request.method=='POST' else runtime.session(request)
  if request.method=='POST':
   try:session.dashboard['weather']=validate_location(await body(request))
   except (ValueError,TypeError):raise HTTPException(400,'invalid_location') from None
  result=await service.get(session.dashboard.get('weather',DEFAULT_LOCATION))
  if not session.alive:raise HTTPException(401,'session_expired')
  return JSONResponse(result)
 async def search(request):
  _,session=runtime.session(request)
  now=time.monotonic()
  if now-session.dashboard.get('weather_search',0)<2:raise HTTPException(429,'rate_limited')
  session.dashboard['weather_search']=now
  try:return JSONResponse({'locations':await service.search(request.query_params.get('q',''))})
  except (httpx.HTTPError,ValueError,TypeError,KeyError):raise HTTPException(400,'location_unavailable') from None
 return [Route('/api/dashboard/weather',weather,methods=['GET','POST']),Route('/api/dashboard/weather/search',search)]
