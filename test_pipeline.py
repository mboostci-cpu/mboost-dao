import os, tempfile, unittest, hashlib, zipfile
from io import BytesIO
from unittest.mock import patch
from fastapi.testclient import TestClient
from app import app, DATA_DIR
from job_store import JobStore
from worker import process

class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.client=TestClient(app)
        self.old={key:os.environ.get(key) for key in ('PUBLIC_MODE','APP_USER','APP_PASSWORD_SHA256')}
        for key in self.old:os.environ.pop(key,None)
    def tearDown(self):
        for key,value in self.old.items():
            if value is None:os.environ.pop(key,None)
            else:os.environ[key]=value
    def test_fail_closed(self):
        os.environ['PUBLIC_MODE']='1'
        self.assertEqual(self.client.get('/').status_code,503)
        self.assertEqual(self.client.get('/health').status_code,200)
    def test_auth(self):
        os.environ['APP_USER']='test'
        os.environ['APP_PASSWORD_SHA256']=hashlib.sha256(b'test-password').hexdigest()
        self.assertEqual(self.client.get('/api/cases').status_code,401)
        self.assertEqual(self.client.get('/api/cases',auth=('test','test-password')).status_code,200)
    def test_claim_once_and_interrupt(self):
        store=JobStore(tempfile.mkdtemp());jid=store.submit({'a':1})
        self.assertEqual(store.claim()['id'],jid)
        self.assertIsNone(store.claim())
        store.interrupt_running();self.assertEqual(store.get(jid)['state'],'interrupted')
        self.assertTrue(store.retry(jid));self.assertFalse(store.retry(jid))
    def test_pipeline_bundle(self):
        response=self.client.post('/api/jobs',data={'candidate_name':'TEST PERSON','company':'TEST COMPANY','proposed_roles':'Chef de chantier'},files=[('dao',('dao.txt',b'BTS Batiment')),('candidate_docs',('cv.txt',b'BTS Batiment'))])
        self.assertEqual(response.status_code,202);jid=response.json()['job_id']
        store=JobStore(DATA_DIR/'queue')
        result={'dao_requirements':[{'role':'Chef de chantier','criterion':'BTS','source_id':'S01','page':1,'quote':'BTS Batiment'}],'candidate_facts':[{'field':'diplôme','value':'BTS Batiment','source_id':'S02','page':1,'quote':'BTS Batiment','status':'prouvé'}],'matches':[],'questions':[],'contradictions':[],'next_actions':[]}
        with patch('app.call_model',return_value=(result,{'provider':'test'})):
            process(store.get(jid),store)
        job=self.client.get('/api/jobs/'+jid).json()
        self.assertEqual(job['state'],'done')
        response=self.client.get('/api/cases/'+job['result']['case_id']+'/bundle')
        self.assertEqual(response.status_code,200)
        self.assertEqual(set(zipfile.ZipFile(BytesIO(response.content)).namelist()),{'rapport.json','CV_PER2_BROUILLON.docx','A_LIRE.txt','textes_extraits.json'})
    def test_no_provider_blocks_job(self):
        response=self.client.post('/api/jobs',data={'candidate_name':'TEST'},files={'dao':('dao.txt',b'DAO')})
        store=JobStore(DATA_DIR/'queue');jid=response.json()['job_id']
        with patch.dict(os.environ,{'MODEL_PROVIDER':''}):process(store.get(jid),store)
        self.assertEqual(store.get(jid)['state'],'blocked')
    def test_format_rejected_at_enqueue(self):
        self.assertEqual(self.client.post('/api/jobs',data={'candidate_name':'TEST'},files={'dao':('x.exe',b'x')}).status_code,400)
    def test_cross_site_write_blocked(self):
        self.assertEqual(self.client.post('/api/jobs',headers={'Origin':'https://attacker.invalid'},data={'candidate_name':'TEST'},files={'dao':('dao.txt',b'DAO')}).status_code,403)

    def test_local_pipeline_without_api(self):
        response=self.client.post('/api/jobs',data={'candidate_name':'TEST'},files={'dao':('dao.txt',b'Personnel : chef de chantier. Trois ans requis.')})
        store=JobStore(DATA_DIR/'queue');jid=response.json()['job_id']
        with patch.dict(os.environ,{'MODEL_PROVIDER':'local'}):process(store.get(jid),store)
        self.assertEqual(store.get(jid)['state'],'done')
        case_id=store.get(jid)['result']['case_id']
        report=self.client.get('/api/cases/'+case_id+'/report').json()
        self.assertEqual(report['analysis']['mode'],'extraction_locale_sans_IA')
        self.assertEqual(report['analysis']['matches'],[])
        self.assertEqual(self.client.get('/api/cases/'+case_id+'/bundle').status_code,200)
