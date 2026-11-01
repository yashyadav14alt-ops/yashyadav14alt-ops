from __future__ import annotations
import base64, json, sqlite3
from pathlib import Path
from typing import Any

class Store:
    def __init__(self, path: str = "hooklab.db") -> None:
        self.path = path
        if path != ":memory:": Path(path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    def _connect(self):
        db = sqlite3.connect(self.path, check_same_thread=False); db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys = ON"); return db
    def _init_db(self):
        with self._connect() as db:
            db.executescript("""CREATE TABLE IF NOT EXISTS endpoints(id TEXT PRIMARY KEY,name TEXT NOT NULL,token TEXT NOT NULL UNIQUE,created_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS requests(id TEXT PRIMARY KEY,endpoint_id TEXT NOT NULL REFERENCES endpoints(id) ON DELETE CASCADE,method TEXT NOT NULL,path TEXT NOT NULL,query TEXT NOT NULL,headers TEXT NOT NULL,body BLOB NOT NULL,content_type TEXT,remote_addr TEXT,created_at TEXT NOT NULL,replayed_from TEXT REFERENCES requests(id));
            CREATE INDEX IF NOT EXISTS idx_requests_endpoint_created ON requests(endpoint_id,created_at DESC);""")
    def create_endpoint(self, e):
        with self._connect() as db: db.execute("INSERT INTO endpoints VALUES (?,?,?,?)",(e["id"],e["name"],e["token"],e["created_at"]))
    def list_endpoints(self):
        with self._connect() as db: return [dict(r) for r in db.execute("SELECT id,name,token,created_at FROM endpoints ORDER BY created_at DESC")]
    def get_endpoint_by_token(self, token):
        with self._connect() as db:
            row=db.execute("SELECT * FROM endpoints WHERE token=?",(token,)).fetchone(); return dict(row) if row else None
    def delete_endpoint(self, endpoint_id):
        with self._connect() as db: return db.execute("DELETE FROM endpoints WHERE id=?",(endpoint_id,)).rowcount > 0
    def save_request(self, x):
        with self._connect() as db: db.execute("INSERT INTO requests VALUES (?,?,?,?,?,?,?,?,?,?,?)",(x["id"],x["endpoint_id"],x["method"],x["path"],x["query"],json.dumps(x["headers"]),x["body"],x.get("content_type"),x.get("remote_addr"),x["created_at"],x.get("replayed_from")))
    def list_requests(self, endpoint_id=None, limit=100):
        with self._connect() as db:
            rows=db.execute("SELECT * FROM requests WHERE endpoint_id=? ORDER BY created_at DESC LIMIT ?",(endpoint_id,limit)).fetchall() if endpoint_id else db.execute("SELECT * FROM requests ORDER BY created_at DESC LIMIT ?",(limit,)).fetchall()
            return [self._decode(r) for r in rows]
    def get_request(self, request_id):
        with self._connect() as db:
            row=db.execute("SELECT * FROM requests WHERE id=?",(request_id,)).fetchone(); return self._decode(row) if row else None
    @staticmethod
    def _decode(row):
        x=dict(row); raw=bytes(x["body"]); x["headers"]=json.loads(x["headers"]); x["body_base64"]=base64.b64encode(raw).decode("ascii"); x["body_text"]=raw.decode("utf-8",errors="replace"); x["body_size"]=len(raw); x.pop("body"); return x
