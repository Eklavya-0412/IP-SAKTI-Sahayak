import argparse
import json
from sqlalchemy import select
from .db import SessionLocal
from .models import User, SourceVersion, Source, Chunk, GraphEdge
from .security import passwords
from .corpus import load_manifest, ingest, reference_release, embed_chunks, reprocess_ocr

def main():
    parser=argparse.ArgumentParser(description='IP-SAKTI corpus and account administration')
    sub=parser.add_subparsers(dest='command',required=True)
    p=sub.add_parser('ingest'); p.add_argument('--remote',action='store_true'); p.add_argument('--source'); p.add_argument('--ocr',action='store_true')
    p.add_argument('--pending',action='store_true')
    sub.add_parser('reference-release')
    sub.add_parser('embed')
    sub.add_parser('inventory')
    p=sub.add_parser('ocr');p.add_argument('--source',required=True)
    p=sub.add_parser('create-user'); p.add_argument('--email',required=True); p.add_argument('--role',choices=['user','facilitator','curator','admin'],default='admin')
    args=parser.parse_args()
    with SessionLocal() as db:
        if args.command=='create-user':
            import getpass
            password=getpass.getpass('Password (12+ characters): ')
            if len(password)<12: raise ValueError('Password must contain at least 12 characters.')
            if db.scalar(select(User).where(User.email==args.email.lower())): raise ValueError('User already exists.')
            db.add(User(email=args.email.lower(),password_hash=passwords.hash(password),role=args.role)); db.commit(); print('User created.')
        elif args.command=='ingest':
            manifest=load_manifest(db)
            for entry in manifest['sources']:
                if args.source and entry['id']!=args.source: continue
                if not args.source and bool(entry.get('local_path'))==args.remote: continue
                if args.pending and db.scalar(select(Chunk.id).join(SourceVersion).where(SourceVersion.source_id==entry['id']).limit(1)):continue
                try: result=ingest(db,entry,args.ocr)
                except Exception as error:
                    db.rollback(); result={'status':'failed','error':type(error).__name__+': '+str(error)[:250]}
                print(json.dumps({'source':entry['id'],**result},ensure_ascii=True),flush=True)
        elif args.command=='reference-release':
            result=reference_release(db); print(result.id)
        elif args.command=='embed': print(embed_chunks(db))
        elif args.command=='ocr': print(json.dumps(reprocess_ocr(db,args.source)))
        elif args.command=='inventory':
            for source in db.scalars(select(Source)):
                versions=db.scalars(select(SourceVersion).where(SourceVersion.source_id==source.id)).all()
                print(json.dumps({'id':source.id,'title':source.title,'versions':[{'id':v.id,'status':v.review_status,'quality':v.quality} for v in versions]}))

if __name__=='__main__': main()
