import base64, hashlib, hmac, os
from urllib.parse import urlsplit
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
class AccessControl(BaseHTTPMiddleware):
    async def dispatch(self,request,call_next):
        user=os.getenv('APP_USER','');digest=os.getenv('APP_PASSWORD_SHA256','')
        public=os.getenv('PUBLIC_MODE','0')=='1'
        if request.url.path=='/health':return await call_next(request)
        if public and (not user or not digest):return Response('Configuration accès incomplète',status_code=503)
        if user and digest:
            try:
                scheme,value=request.headers.get('authorization','').split(' ',1)
                name,password=base64.b64decode(value,validate=True).decode().split(':',1)
                valid=scheme.lower()=='basic' and hmac.compare_digest(name,user) and hmac.compare_digest(hashlib.sha256(password.encode()).hexdigest(),digest)
            except (ValueError,UnicodeError):valid=False
            if not valid:return Response('Authentification requise',status_code=401,headers={'WWW-Authenticate':'Basic realm="MBOOST CV DAO", charset="UTF-8"'})
        origin=request.headers.get('origin')
        if request.method not in ('GET','HEAD','OPTIONS') and origin and urlsplit(origin).netloc != request.headers.get('host'):
            return Response('Origine refusée',status_code=403)
        response=await call_next(request)
        response.headers['Cache-Control']='no-store'
        response.headers['X-Content-Type-Options']='nosniff'
        response.headers['Referrer-Policy']='same-origin'
        return response
