import test from 'node:test'
import assert from 'node:assert/strict'
import ts from 'typescript'
import {readFile,mkdir,writeFile,rm} from 'node:fs/promises'
const dir=new URL('./.cache/',import.meta.url)
await mkdir(dir,{recursive:true})
const moduleURL=new URL('lib.mjs',dir)
const source=await readFile(new URL('../src/lib.ts',import.meta.url),'utf8')
await writeFile(moduleURL,ts.transpileModule(source,{compilerOptions:{target:ts.ScriptTarget.ES2022,module:ts.ModuleKind.ES2022}}).outputText)
let count=0
const fresh=()=>import(moduleURL.href+'?case='+count++)
const json=data=>new Response(JSON.stringify(data),{headers:{'Content-Type':'application/json'}})

test('concurrent POSTs wait for one session and use its token',async()=>{
 const lib=await fresh();let resolveSession;const calls=[]
 globalThis.fetch=async(path,options)=>{
  calls.push({path,options})
  if(path.endsWith('/auth/session'))return await new Promise(resolve=>{resolveSession=resolve})
  assert.equal(options.headers.get('X-CSRF-Token'),'first-token')
  assert.equal(options.credentials,'include')
  return json({ok:true})
 }
 const bootstrap=lib.api('/auth/session')
 const first=lib.post('/questions',{}),second=lib.post('/assessments/classification',{})
 await Promise.resolve();assert.equal(calls.length,1)
 resolveSession(json({csrf_token:'first-token',user:null}))
 await Promise.all([bootstrap,first,second]);assert.equal(calls.length,3)
})

test('bootstrap failure prevents POST, and subsequent attempt can retry',async()=>{
 const lib=await fresh();let sessions=0,posts=0
 globalThis.fetch=async(path)=>{
  if(path.endsWith('/auth/session')){sessions++;return sessions===1?new Response('Offline',{status:503}):json({csrf_token:'retry'})}
  posts++;return json({ok:true})
 }
 await assert.rejects(lib.post('/questions',{}),/Offline/);assert.equal(posts,0)
 await lib.post('/questions',{});assert.equal(sessions,2);assert.equal(posts,1)
})

test('login rotation updates memory and logout invalidates bootstrap',async()=>{
 const lib=await fresh();let sessions=0
 globalThis.fetch=async(path,options)=>{
  if(path.endsWith('/auth/session'))return json({csrf_token:'session-'+(++sessions)})
  if(path.endsWith('/auth/login'))return json({csrf_token:'rotated'})
  if(path.endsWith('/questions'))assert.equal(options.headers.get('X-CSRF-Token'),'rotated')
  return json({ok:true})
 }
 await lib.post('/auth/login',{});await lib.post('/questions',{});await lib.post('/auth/logout',{});await lib.api('/auth/session')
 assert.equal(sessions,2)
})

test('SSE handles split UTF-8, stages, and structured answer',async()=>{
 const lib=await fresh(),stages=[]
 const answer={claims:[],citations:[],heading:'नमस्ते'}
 const data=new TextEncoder().encode('event: stage\ndata: {"stage":"Searching"}\n\nevent: answer\ndata: '+JSON.stringify(answer)+'\n\n')
 globalThis.fetch=async(path)=>path.endsWith('/auth/session')?json({csrf_token:'sse'}):new Response(new ReadableStream({start(controller){for(const byte of data)controller.enqueue(new Uint8Array([byte]));controller.close()}}))
 assert.deepEqual(await lib.streamQuestion({query:'patent',jurisdiction:'india',market:'treaties',language:'en',previous_questions:[]},s=>stages.push(s)),answer)
 assert.deepEqual(stages,['Searching'])
})

test.after(async()=>{await rm(dir,{recursive:true,force:true})})
