from starlette.routing import Route
from starlette.responses import JSONResponse,Response
from starlette.exceptions import HTTPException
from .service import Photos,clear_photos
from ..ssh.service import SourceError

def routes(runtime,body):
 service=runtime.photos=Photos(runtime.computer)
 async def photos(request):
  _,session=runtime.mutation(request,True) if request.method=='POST' else runtime.session(request,True)
  try:
   if request.method=='POST':
    data=await body(request)
    if data=={'action':'revoke'}:clear_photos(session);return JSONResponse({'state':'not_configured','files':[]})
    await service.configure(session,data)
   return JSONResponse(await service.listing(session))
  except SourceError as exc:raise HTTPException(404 if exc.code=='not_found' else 409,exc.code) from None
  except (ValueError,OSError,TimeoutError):raise HTTPException(400,'photo_unavailable') from None
 async def image(request):
  _,session=runtime.session(request,True)
  try:return Response(await service.image(session,request.path_params['id']),media_type='image/jpeg',headers={'Cache-Control':'no-store'})
  except SourceError as exc:raise HTTPException(404 if exc.code=='not_found' else 409,exc.code) from None
  except (ValueError,OSError,TimeoutError):raise HTTPException(400,'photo_unavailable') from None
 return [Route('/api/dashboard/photos',photos,methods=['GET','POST']),Route('/api/dashboard/photos/{id}',image)]
