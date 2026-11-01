from __future__ import annotations
import base64, os, secrets, uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from .store import Store
BASE_DIR=Path(__file__).resolve().parent.parent
store=Store(os.getenv("HOOKLAB_DB",str(BASE_DIR/"data"/"hooklab.db")))
MAX_BODY_BYTES=int(os.getenv("HOOKLAB_MAX_BODY_BYTES",str(1024*1024)))
app=FastAPI(title="Hooklab API",version="0.1.0",description="A local-first webhook inspection workbench.")
app.mount("/static",StaticFiles(directory=BASE_DIR/"static"),name="static")
def now_iso(): return datetime.now(timezone.utc).isoformat()
def public_request(x):
    x=dict(x); x.pop("body_text",None); x.pop("body_base64",None); return x
class EndpointCreate(BaseModel): name:str=Field(default="My webhook",min_length=1,max_length=80)
class ReplayCreate(BaseModel): target_endpoint_id:str=Field(min_length=1)
@app.get("/",include_in_schema=False)
async def dashboard(): return FileResponse(BASE_DIR/"static"/"index.html")
@app.get("/health")
async def health(): return {"status":"ok","service":"hooklab"}
@app.post("/api/endpoints",status_code=201)
async def create_endpoint(payload:EndpointCreate):
    e={"id":uuid.uuid4().hex[:12],"name":payload.name,"token":secrets.token_urlsafe(18),"created_at":now_iso()}; store.create_endpoint(e); return {**e,"url":f"/hook/{e['token']}"}
@app.get("/api/endpoints")
async def list_endpoints(): return [{**e,"url":f"/hook/{e['token']}"} for e in store.list_endpoints()]
@app.delete("/api/endpoints/{endpoint_id}",status_code=204)
async def delete_endpoint(endpoint_id:str):
    if not store.delete_endpoint(endpoint_id): raise HTTPException(404,"Endpoint not found")
@app.get("/api/requests")
async def list_requests(endpoint_id:str|None=None,limit:int=100):
    if not 1<=limit<=500: raise HTTPException(422,"limit must be between 1 and 500")
    return [public_request(x) for x in store.list_requests(endpoint_id,limit)]
@app.get("/api/requests/{request_id}")
async def get_request(request_id:str):
    x=store.get_request(request_id)
    if not x: raise HTTPException(404,"Request not found")
    return x
@app.post("/api/requests/{request_id}/replay",status_code=201)
async def replay_request(request_id:str,payload:ReplayCreate):
    original=store.get_request(request_id)
    if not original: raise HTTPException(404,"Request not found")
    target=next((e for e in store.list_endpoints() if e["id"]==payload.target_endpoint_id),None)
    if not target: raise HTTPException(404,"Target endpoint not found")
    replay={"id":uuid.uuid4().hex,"endpoint_id":target["id"],"method":original["method"],"path":original["path"],"query":original["query"],"headers":original["headers"],"body":base64.b64decode(original["body_base64"]),"content_type":original.get("content_type"),"remote_addr":"hooklab-replay","created_at":now_iso(),"replayed_from":request_id}
    store.save_request(replay); return {"id":replay["id"],"replayed_from":request_id,"target_endpoint_id":target["id"]}
@app.api_route("/hook/{token}",methods=["GET","POST","PUT","PATCH","DELETE","OPTIONS","HEAD"])
@app.api_route("/hook/{token}/{path:path}",methods=["GET","POST","PUT","PATCH","DELETE","OPTIONS","HEAD"])
async def capture_webhook(token:str,request:Request,path:str=""):
    endpoint=store.get_endpoint_by_token(token)
    if not endpoint: raise HTTPException(404,"Unknown webhook endpoint")
    body=await request.body()
    if len(body)>MAX_BODY_BYTES: raise HTTPException(413,f"Payload exceeds {MAX_BODY_BYTES} bytes")
    x={"id":uuid.uuid4().hex,"endpoint_id":endpoint["id"],"method":request.method,"path":"/"+path,"query":str(request.url.query),"headers":dict(request.headers),"body":body,"content_type":request.headers.get("content-type"),"remote_addr":request.client.host if request.client else None,"created_at":now_iso(),"replayed_from":None}
    store.save_request(x); return JSONResponse({"received":True,"request_id":x["id"]})
