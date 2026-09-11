"""Package code and submission artifacts; exclude credentials, runtime data and caches."""
import hashlib,json,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
allowed_dirs={'backend','frontend','corpus','docs','scripts','deploy','evals','Resources','.github','deliverables'}
excluded={'node_modules','dist','__pycache__','.pytest_cache','.venv','data','tmp','.git','.agents','.codex'}
root_files={'README.md','.env.example','.gitignore','.dockerignore','compose.yaml'}
paths=[]
for folder in allowed_dirs:
    base=ROOT/folder
    if not base.exists():continue
    for path in base.rglob('*'):
        rel=path.relative_to(ROOT)
        if not path.is_file() or any(part in excluded for part in rel.parts):continue
        if path.suffix in {'.pyc','.zip','.log'} or path.name.startswith('.env'):continue
        paths.append(path)
paths += [ROOT/name for name in root_files if (ROOT/name).exists()]
manifest=[{'path':str(p.relative_to(ROOT)).replace('\\','/'),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size} for p in sorted(paths)]
target=ROOT/'deliverables'/'IP-SAKTI-Source-and-Submission.zip'
with zipfile.ZipFile(target,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
    for p in sorted(paths):archive.write(p,p.relative_to(ROOT).as_posix())
    archive.writestr('PACKAGE-MANIFEST.json',json.dumps(manifest,indent=2))
with zipfile.ZipFile(target) as archive:
    assert archive.testzip() is None
    assert not any('/data/' in '/'+n or n.endswith('/.env') or n=='.env' or n.endswith('.env.docker') for n in archive.namelist())
print(f'{target}: {len(paths)} files, {target.stat().st_size} bytes; archive verified.')
