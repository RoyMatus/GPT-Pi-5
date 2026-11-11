"""Authenticated Computer routes; shared SSH service is also the photo transport owner."""
from starlette.routing import Route
from starlette.responses import JSONResponse
from starlette.exceptions import HTTPException
from ..ssh.service import ComputerService,SourceError

def routes(runtime,body):
 service=runtime.computer=ComputerService(runtime.settings.data_dir)
 async def computer(request):
  _,session=runtime.mutation(request,True) if request.method=='POST' else runtime.session(request,True)
  try:
   state=service.state(session)
   if request.method=='POST':
    data=await body(request)
    if not session.alive:raise HTTPException(401,'session_expired')
    action=data.pop('action',None)
    if action=='configure':state.configure(data)
    elif action=='disable' and not data:state.disable()
    elif action=='remove' and not data:state.disable(remove=True)
    elif action=='rotate' and not data:
     state.reset()
     for name in ['telemetry.key','photos.key']:(state.path/name).unlink(missing_ok=True)
    else:raise ValueError('invalid_profile')
    return JSONResponse(state.public())
   return JSONResponse(await state.collect(session))
  except ValueError:raise HTTPException(400,'invalid_profile') from None
  except SourceError as exc:raise HTTPException(401 if exc.code=='session_expired' else 409,exc.code) from None
  except OSError:raise HTTPException(503,'source_storage') from None
 return [Route('/api/dashboard/computer',computer,methods=['GET','POST'])]
