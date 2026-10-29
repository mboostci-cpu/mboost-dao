"""Persistent single-worker queue. Interrupted calls require manual review."""
import json, sqlite3, time, uuid
from pathlib import Path

class JobStore:
    def __init__(self, root):
        self.root=Path(root); self.root.mkdir(parents=True,exist_ok=True)
        self.db=self.root/'jobs.sqlite3'
        with self.connect() as con:
            con.execute('CREATE TABLE IF NOT EXISTS jobs (id TEXT PRIMARY KEY, state TEXT NOT NULL, payload TEXT NOT NULL, result TEXT, created REAL, updated REAL)')
    def connect(self):
        con=sqlite3.connect(self.db,timeout=30); con.row_factory=sqlite3.Row
        return con
    def submit(self, payload, job_id=None):
        job_id=job_id or uuid.uuid4().hex[:12]; now=time.time()
        with self.connect() as con:
            con.execute('INSERT INTO jobs VALUES (?, ?, ?, NULL, ?, ?)',(job_id,'queued',json.dumps(payload,ensure_ascii=False),now,now))
        return job_id
    def get(self, job_id):
        with self.connect() as con: row=con.execute('SELECT * FROM jobs WHERE id=?',(job_id,)).fetchone()
        if row is None:return None
        result=dict(row);result['payload']=json.loads(result['payload']);result['result']=json.loads(result['result']) if result['result'] else None
        return result
    def claim(self):
        with self.connect() as con:
            con.execute('BEGIN IMMEDIATE')
            row=con.execute("SELECT id FROM jobs WHERE state='queued' ORDER BY created LIMIT 1").fetchone()
            if row is None:return None
            con.execute("UPDATE jobs SET state='running',updated=? WHERE id=?",(time.time(),row['id']))
        return self.get(row['id'])
    def finish(self,job_id,state,result):
        with self.connect() as con:
            con.execute('UPDATE jobs SET state=?,result=?,updated=? WHERE id=?',(state,json.dumps(result,ensure_ascii=False),time.time(),job_id))
    def interrupt_running(self):
        with self.connect() as con:
            con.execute("UPDATE jobs SET state='interrupted', updated=? WHERE state='running'",(time.time(),))
    def retry(self,job_id):
        with self.connect() as con:
            count=con.execute("UPDATE jobs SET state='queued',result=NULL,updated=? WHERE id=? AND state IN ('blocked','failed','interrupted')",(time.time(),job_id)).rowcount
        return bool(count)
