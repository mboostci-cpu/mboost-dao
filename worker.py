"""Run one durable worker. No remote execution from document instructions."""
import asyncio, fcntl, json, os, time
from io import BytesIO
from pathlib import Path
from fastapi import UploadFile
from app import DATA_DIR, analyze
from job_store import JobStore


def process(job,store):
    payload=job['payload'];folder=store.root/job['id']
    async def execute():
        dao_path=folder/payload['dao']
        dao=UploadFile(filename=payload['dao'],file=BytesIO(dao_path.read_bytes()))
        documents=[UploadFile(filename=name,file=BytesIO((folder/name).read_bytes())) for name in payload['documents']]
        return await analyze(candidate_name=payload['candidate_name'],company=payload.get('company',''),proposed_roles=payload.get('proposed_roles',''),diploma=payload.get('diploma',''),companies=payload.get('companies',''),dao=dao,candidate_docs=documents)
    try:
        response=asyncio.run(execute());case=json.loads(response.body)
        state='done' if case['status']=='analysis_ready' else 'blocked'
        store.finish(job['id'],state,{'case_id':case['case_id'],'status':case['status']})
    except Exception as exc:
        # Do not log document content, keys or raw provider responses.
        store.finish(job['id'],'failed',{'error_type':type(exc).__name__,'message':'Échec du traitement ; vérifier les formats, limites et la configuration.'})


def main():
    store=JobStore(DATA_DIR/'queue')
    lock=open(store.root/'worker.lock','w')
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    store.interrupt_running()
    while True:
        job=store.claim()
        if job:process(job,store)
        else:time.sleep(2)
if __name__=='__main__': main()
