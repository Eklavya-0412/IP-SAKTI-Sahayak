"""Binary-safe local Docker health and isolated database/document restore rehearsal."""
import argparse,hashlib,io,json,subprocess,tarfile,time
from pathlib import Path
import httpx
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--env-file',default='.env');args=p.parse_args()
base=['docker','compose','--env-file',args.env_file]
def run(*cmd):return subprocess.run(base+list(cmd),cwd=ROOT,check=True,capture_output=True).stdout
stamp=time.strftime('%Y%m%d%H%M%S',time.gmtime());backup=ROOT/'data'/'backups'/stamp;backup.mkdir(parents=True)
dump=run('exec','-T','db','pg_dump','-U','ipsakti','-d','ipsakti','-Fc');(backup/'database.dump').write_bytes(dump)
archive=run('exec','-T','api','tar','-czf','-','-C','/app/data','snapshots');(backup/'documents.tar.gz').write_bytes(archive)
restore='ipsakti_restore_'+stamp
run('exec','-T','db','createdb','-U','ipsakti',restore)
subprocess.run(base+['exec','-T','db','pg_restore','-U','ipsakti','-d',restore,'--no-owner','--exit-on-error'],input=dump,cwd=ROOT,check=True,capture_output=True)
counts={}
for database in ['ipsakti',restore]:
    counts[database]=run('exec','-T','db','psql','-U','ipsakti','-d',database,'-tAc','SELECT count(*) FROM source_versions').decode().strip()
assert len(set(counts.values()))==1
files=0
with tarfile.open(fileobj=io.BytesIO(archive),mode='r:gz') as tar:
    for member in tar.getmembers():
        if member.isfile():
            data=tar.extractfile(member).read();assert hashlib.sha256(data).hexdigest()==Path(member.name).stem;files+=1
assert files>0
with httpx.Client(base_url='http://localhost:8080',timeout=120) as client:
    health=client.get('/api/v1/health');health.raise_for_status()
    session=client.get('/api/v1/auth/session').json();client.headers['X-CSRF-Token']=session['csrf_token'];client.headers['Origin']='http://localhost:8080'
    tick=time.perf_counter();response=client.post('/api/v1/questions',json={'query':'traditional knowledge patent formulation'});response.raise_for_status()
    answer=response.json();assert answer['mode']=='retrieval';assert answer['citations']
    for cite in answer['citations']:client.get('/api/v1/sources/chunks/'+cite['id']).raise_for_status()
report={'timestamp':stamp,'health':health.json(),'source_version_counts':counts,'document_checksums_verified':files,'backup_directory':str(backup.relative_to(ROOT)),
 'isolated_restore_database':restore,'answer_mode':answer['mode'],'citation_count':len(answer['citations']),'http_query_ms':round((time.perf_counter()-tick)*1000,2),
 'status':'passed','limitations':['Database restored into a separate named database; live database untouched.','Document archive contents read and checked against SHA-256 filenames; full service cutover not performed.','Restore database and private backups intentionally retained for operator inspection.']}
(ROOT/'docs'/'deployment-results.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
