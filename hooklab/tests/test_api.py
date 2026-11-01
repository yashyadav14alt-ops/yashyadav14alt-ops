import base64,importlib
from fastapi.testclient import TestClient

def client_for(tmp_path,monkeypatch):
 monkeypatch.setenv('HOOKLAB_DB',str(tmp_path/'test.db'))
 import app.main as main
 importlib.reload(main)
 return TestClient(main.app)
def test_health_and_endpoint_creation(tmp_path,monkeypatch):
 c=client_for(tmp_path,monkeypatch);assert c.get('/health').json()['status']=='ok';e=c.post('/api/endpoints',json={'name':'Stripe test'});assert e.status_code==201;assert e.json()['url']=='/hook/'+e.json()['token']
def test_capture_and_inspect_webhook(tmp_path,monkeypatch):
 c=client_for(tmp_path,monkeypatch);e=c.post('/api/endpoints',json={'name':'Orders'}).json();r=c.post(e['url']+'/orders',params={'source':'test'},headers={'x-event':'order.created'},json={'order_id':42});assert r.status_code==200;x=c.get('/api/requests/'+r.json()['request_id']).json();assert x['method']=='POST' and x['path']=='/orders';assert x['headers']['x-event']=='order.created';assert x['query']=='source=test';assert 'order_id' in x['body_text']
def test_unknown_endpoint_and_request_return_404(tmp_path,monkeypatch):
 c=client_for(tmp_path,monkeypatch);assert c.post('/hook/invalid').status_code==404;assert c.get('/api/requests/missing').status_code==404
def test_replay_copies_event_to_another_endpoint(tmp_path,monkeypatch):
 c=client_for(tmp_path,monkeypatch);a=c.post('/api/endpoints',json={'name':'A'}).json();b=c.post('/api/endpoints',json={'name':'B'}).json();r=c.post(a['url'],json={'event':'paid'}).json();assert c.post('/api/requests/'+r['request_id']+'/replay',json={'target_endpoint_id':b['id']}).status_code==201;copied=c.get('/api/requests',params={'endpoint_id':b['id']}).json();assert len(copied)==1 and copied[0]['replayed_from']==r['request_id']
def test_replay_preserves_binary_payload(tmp_path,monkeypatch):
 c=client_for(tmp_path,monkeypatch);a=c.post('/api/endpoints',json={'name':'A'}).json();b=c.post('/api/endpoints',json={'name':'B'}).json();raw=b'\\xff\\x00\\x81payload';r=c.post(a['url'],content=raw).json();c.post('/api/requests/'+r['request_id']+'/replay',json={'target_endpoint_id':b['id']});copied=c.get('/api/requests',params={'endpoint_id':b['id']}).json()[0];detail=c.get('/api/requests/'+copied['id']).json();assert base64.b64decode(detail['body_base64'])==raw
def test_oversized_payload_is_rejected(tmp_path,monkeypatch):
 monkeypatch.setenv('HOOKLAB_MAX_BODY_BYTES','8');c=client_for(tmp_path,monkeypatch);e=c.post('/api/endpoints',json={'name':'Limited'}).json();assert c.post(e['url'],content=b'0123456789').status_code==413