import {useEffect,useRef,useState} from 'react'
import {BookOpen,FlaskConical,Leaf,MessageSquare,ShieldCheck,FolderOpen,ArrowUpRight,ArrowUp,Globe2,PanelLeftClose,PanelLeftOpen,Plus,Search,Settings2,Library,ClipboardCheck,Database,Check,ChevronRight,ExternalLink,Download,Mic,Square,Volume2,Bookmark,ThumbsUp,Flag,LoaderCircle,Info,LogIn,X,Scale,LockKeyhole} from 'lucide-react'
import {api,post,setCSRF,downloadJSON} from './lib'
import type {Lang,Jurisdiction,Market,Citation,Answer,Turn} from './lib'
import {t} from './i18n'
import type {Key} from './i18n'
import {Button} from './components/ui/button'
import {Dialog,DialogContent,DialogTitle,DialogDescription} from './components/ui/dialog'
import {AssessmentPage,LibraryPage,CasesPage,ReviewPage,SettingsPage,AdminPage,PriorPage} from './pages'

type Page='assistant'|'classification'|'abs'|'sources'|'cases'|'reviews'|'admin'|'settings'|'prior'
const nav=[{id:'assistant',icon:MessageSquare},{id:'classification',icon:FlaskConical},{id:'abs',icon:ShieldCheck},{id:'sources',icon:Library},{id:'prior',icon:Search},{id:'cases',icon:FolderOpen}] as const

export default function App(){
 const [lang,setLang]=useState<Lang>((localStorage.getItem('ipsakti-language') as Lang)||'en')
 const [page,setPage]=useState<Page>('assistant')
 const [jurisdiction,setJurisdiction]=useState<Jurisdiction>('india')
 const [market,setMarket]=useState<Market>('treaties')
 const [user,setUser]=useState<any>(null)
 const [caps,setCaps]=useState<any>(null)
 const [coverage,setCoverage]=useState<any>(null)
 const [online,setOnline]=useState(false)
 const [auth,setAuth]=useState(false)
 const [menu,setMenu]=useState(false)
 const [error,setError]=useState('')
 const [notice,setNotice]=useState('')
 const [citation,setCitation]=useState<Citation|null>(null)
 const [histories,setHistories]=useState<Record<string,Turn[]>>({})
 const [seed,setSeed]=useState('')
 const [activeCase,setActiveCase]=useState<any>(null)
 const initial=useRef(false)
 const tr=(key:Key)=>t(key,lang)
 const key=`${jurisdiction}:${jurisdiction==='india'?'treaties':market}:${lang}`
 const turns=histories[key]||[]
 const fail=(e:unknown)=>setError(e instanceof Error?e.message:String(e))
 async function refresh(){try{const [c,v]=await Promise.all([api('/capabilities'),api('/coverage')]);setCaps(c);setCoverage(v);setOnline(true)}catch(e){fail(e);setOnline(false)}}
 async function bootstrap(){try{const s=await api('/auth/session');setCSRF(s.csrf_token);setUser(s.user);await refresh()}catch(e){fail(e);setOnline(false)}}
 useEffect(()=>{if(!initial.current){initial.current=true;void bootstrap()}},[])
 useEffect(()=>{document.documentElement.lang=lang;localStorage.setItem('ipsakti-language',lang)},[lang])
 useEffect(()=>{if(notice){const id=setTimeout(()=>setNotice(''),4500);return()=>clearTimeout(id)}},[notice])
 function viewCitation(value:Citation){setCitation(value);api<Citation>('/sources/chunks/'+value.id).then(setCitation).catch(fail)}
 function navigate(id:Page){setPage(id);setMenu(false)}
 async function signOut(){setActiveCase(null);try{await post('/auth/logout',{});setHistories({});await bootstrap();setNotice(tr('signOut'))}catch(e){fail(e)}}
 async function saveCase(){
  if(!user){setAuth(true);return}
  if(!turns.length)return
  try{await post('/cases',{title:turns[0].question.slice(0,180),jurisdiction,market:jurisdiction==='india'?'treaties':market,confidential:true,content:{history:turns}});setNotice(tr('saved'));setPage('cases')}catch(e){fail(e)}
 }
 const shared={lang,user,onError:fail,onNotice:setNotice,onAuth:()=>setAuth(true),onCitation:viewCitation}
 return <div className="app-shell">
  <a className="skip-link" href="#main">Skip to content</a>
  {menu&&<button className="mobile-scrim" aria-label={tr('close')} onClick={()=>setMenu(false)}/>}
  <aside className={`sidebar ${menu?'sidebar-open':''}`}>
   <button className="brand" onClick={()=>navigate('assistant')} aria-label="IP-SAKTI Sahayak home"><span className="brand-icon"><Leaf size={25} strokeWidth={1.6}/></span><span><strong>IP-SAKTI</strong><small>SAHAYAK</small></span></button>
   <div className="sidebar-tagline">{tr('tagline')}</div>
   <Button variant="outline" className="new-chat" onClick={()=>{setActiveCase(null);setHistories({...histories,[key]:[]});navigate('assistant')}}><Plus size={17}/>{tr('newChat')}</Button>
   <p className="nav-label">{tr('workspace')}</p>
   <nav aria-label={tr('workspace')}>{nav.map(({id,icon:Icon})=><button key={id} className={`nav-item ${page===id?'active':''}`} onClick={()=>navigate(id)}><Icon size={19}/><span>{tr(id)}</span>{page===id&&<span className="nav-active-dot"/>}</button>)}</nav>
   {user&&<div className="secondary-nav"><button className={`nav-item ${page==='reviews'?'active':''}`} onClick={()=>navigate('reviews')}><ClipboardCheck size={19}/>{tr('reviews')}</button>{['curator','admin'].includes(user.role)&&<button className={`nav-item ${page==='admin'?'active':''}`} onClick={()=>navigate('admin')}><Database size={19}/>{tr('admin')}</button>}</div>}
   <div className="sidebar-bottom"><div className="source-status"><span className={online?'status-dot':'status-dot offline'}/><div><strong>{tr(online?'connected':'offline')}</strong><small>{coverage?.sources??'—'} {tr('sourceCount').toLowerCase()}</small></div></div><button className={`nav-item ${page==='settings'?'active':''}`} onClick={()=>navigate('settings')}><Settings2 size={18}/>{tr('settings')}</button>
   <button className="account-button" onClick={()=>user?signOut():setAuth(true)}><span className="avatar">{user?user.email[0].toUpperCase():<LogIn size={18}/>}</span><span><strong>{user?user.email:tr('guest')}</strong><small>{user?tr('signOut'):tr('signIn')}</small></span><ChevronRight size={15}/></button></div>
  </aside>
  <div className="main-shell">
   <header className="topbar"><div className="breadcrumb"><button className="mobile-toggle" aria-label="Menu" onClick={()=>setMenu(!menu)}>{menu?<PanelLeftClose size={22}/>:<PanelLeftOpen size={22}/>}</button><span>{tr('workspace')}</span><ChevronRight size={13}/><strong>{tr(page)}</strong></div><div className="header-actions"><span className="pilot-pill">PILOT</span><label className="language-control"><Globe2 size={16}/><select aria-label="Language" value={lang} onChange={e=>setLang(e.target.value as Lang)}><option value="en">English</option><option value="hi">हिन्दी</option><option value="mr">मराठी</option></select></label></div></header>
   <main id="main">
    {error&&<div className="error-banner" role="alert"><Info size={18}/><div><strong>{tr('error')}</strong><p>{error}</p></div><button aria-label={tr('close')} onClick={()=>setError('')}><X size={18}/></button></div>}
    {page==='assistant'&&<>
     <div className="scope-bar"><div className="scope-toggle" aria-label="Jurisdiction"><button aria-pressed={jurisdiction==='india'} onClick={()=>{setActiveCase(null);setJurisdiction('india')}} className={jurisdiction==='india'?'selected':''}><span className="india-dot"/>{tr('india')}</button><button aria-pressed={jurisdiction==='international'} onClick={()=>{setActiveCase(null);setJurisdiction('international')}} className={jurisdiction==='international'?'selected':''}><Globe2 size={15}/>{tr('international')}</button></div>{jurisdiction==='international'&&<select className="market-select" aria-label="International market" value={market} onChange={e=>{setActiveCase(null);setMarket(e.target.value as Market)}}>{(['treaties','us','eu','uk'] as const).map(m=><option key={m} value={m}>{tr(m)}</option>)}</select>}<span className="scope-description"><LockKeyhole size={13}/>{tr('scopeNote')}</span></div>
     <Chat caseId={activeCase?.id} lang={lang} jurisdiction={jurisdiction} market={market} turns={turns} setTurns={value=>setHistories(h=>({...h,[key]:value}))} caps={caps} seed={seed} setSeed={setSeed} onCitation={viewCitation} onError={fail} onNotice={setNotice} onSave={saveCase} onNavigate={navigate}/>
    </>}
    {page==='classification'&&<AssessmentPage key={`classify-${lang}`} kind="classification" {...shared}/>}
    {page==='abs'&&<AssessmentPage key={`abs-${lang}`} kind="abs" {...shared}/>}
    {page==='sources'&&<LibraryPage {...shared} coverage={coverage}/>}
    {page==='cases'&&<CasesPage {...shared} onOpenCase={c=>{setActiveCase(c);setJurisdiction(c.jurisdiction);setMarket(c.market);setHistories(h=>({...h,[`${c.jurisdiction}:${c.market}:${lang}`]:c.content.history||[]}));navigate('assistant')}}/>}
    {page==='reviews'&&<ReviewPage {...shared}/>}
    {page==='prior'&&<PriorPage {...shared}/>}
    {page==='settings'&&<SettingsPage {...shared} caps={caps} onDeleted={()=>{setHistories({});void bootstrap()}}/>}
    {page==='admin'&&<AdminPage {...shared} onRefresh={refresh}/>}
   </main>
   <footer className="app-footer"><Scale size={14}/><span>{tr('disclaimer')}</span><span className="footer-version">IP-SAKTI · v1.0</span></footer>
  </div>
  <Dialog open={!!citation} onOpenChange={open=>!open&&setCitation(null)}><DialogContent sheet><DialogTitle>{tr('snapshot')}</DialogTitle><DialogDescription>{tr('original')}</DialogDescription>{citation&&<div className="citation-details"><span className="eyebrow">{citation.publisher}</span><h2>{citation.title}</h2><p className="locator"><BookOpen size={16}/>{citation.locator}{citation.page?` · PDF ${citation.page}`:''}</p><span className={`badge ${citation.review_status==='approved'?'green':'amber'}`}>{citation.review_status==='approved'?tr('approved'):tr('referenceOnly')}</span><blockquote>{citation.excerpt}</blockquote><dl><dt>{tr('retrieved')}</dt><dd>{new Date(citation.retrieved_at).toLocaleDateString()}</dd><dt>{tr('reviewStatus')}</dt><dd>{citation.review_note||citation.review_status}</dd>{citation.checksum&&<><dt>{tr('checksum')}</dt><dd className="hash">{citation.checksum}</dd></>}</dl><div className="button-row"><Button variant="outline" asChild><a href={citation.url} target="_blank" rel="noreferrer">{tr('official')}<ExternalLink size={15}/></a></Button>{citation.file_url&&<Button asChild><a href={citation.file_url} target="_blank" rel="noreferrer">{tr('download')}<Download size={15}/></a></Button>}</div></div>}</DialogContent></Dialog>
  <AuthDialog open={auth} onOpenChange={setAuth} lang={lang} onError={fail} onDone={value=>{setUser(value);setAuth(false);setNotice(tr('saved'))}}/>
  {notice&&<div className="toast" role="status"><Check size={18}/>{notice}</div>}
 </div>
}

function Chat({caseId,lang,jurisdiction,market,turns,setTurns,caps,seed,setSeed,onCitation,onError,onNotice,onSave,onNavigate}:{caseId?:string;lang:Lang;jurisdiction:Jurisdiction;market:Market;turns:Turn[];setTurns:(v:Turn[])=>void;caps:any;seed:string;setSeed:(v:string)=>void;onCitation:(c:Citation)=>void;onError:(e:unknown)=>void;onNotice:(v:string)=>void;onSave:()=>void;onNavigate:(p:Page)=>void}){
 const tr=(k:Key)=>t(k,lang)
 const [query,setQuery]=useState(''),[busy,setBusy]=useState(false),[cloud,setCloud]=useState(false),[confidential,setConfidential]=useState(false)
 const [recording,setRecording]=useState(false),[audio,setAudio]=useState<string|null>(null)
 const end=useRef<HTMLDivElement>(null),voice=useRef<{context:AudioContext;stream:MediaStream;processor:ScriptProcessorNode;chunks:Float32Array[];source:MediaStreamAudioSourceNode}|null>(null)
 useEffect(()=>{if(seed){setQuery(seed);setSeed('')}},[seed])
 useEffect(()=>{end.current?.scrollIntoView({behavior:'smooth',block:'nearest'})},[turns.length])
 useEffect(()=>()=>{voice.current?.stream.getTracks().forEach(t=>t.stop());void voice.current?.context.close()},[])
 async function send(value=query){if(busy||value.trim().length<3)return;setBusy(true);setQuery('');try{const answer=await post<Answer>('/questions',{query:value,jurisdiction,market:jurisdiction==='india'?'treaties':market,language:lang,confidential:confidential||!!caseId,cloud_consent:cloud,case_id:caseId,previous_questions:turns.slice(-4).map(t=>t.question)});setTurns([...turns,{question:value,answer}])}catch(e){onError(e);setQuery(value)}finally{setBusy(false)}}
 async function feedback(answer:Answer,reason:string){try{await post('/feedback',{trace_id:answer.trace_id,rating:reason==='helpful'?5:2,reason});onNotice(tr('feedbackSaved'))}catch(e){onError(e)}}
 async function speak(answer:Answer){
  if(!window.confirm(tr('voiceConsent')))return
  try{const r=await post('/language',{task:'tts',source:answer.translation?lang:'en',text:answer.translation||answer.claims.map(c=>c.text).join('\n'),allow_cloud:true,confidential:confidential||!!caseId});setAudio('data:audio/wav;base64,'+r.audio)}catch(e){onError(e)}
 }
 async function record(){
  if(recording&&voice.current){
   const v=voice.current;v.processor.disconnect();v.source.disconnect();v.stream.getTracks().forEach(t=>t.stop());await v.context.close();voice.current=null;setRecording(false)
   const raw=new Float32Array(v.chunks.reduce((n,c)=>n+c.length,0));let offset=0;for(const chunk of v.chunks){raw.set(chunk,offset);offset+=chunk.length}
   const wav=encodeWav(raw,v.context.sampleRate);let binary='';const bytes=new Uint8Array(wav);for(let i=0;i<bytes.length;i++)binary+=String.fromCharCode(bytes[i])
   setBusy(true);try{const r=await post('/language',{task:'asr',source:lang,audio:btoa(binary),allow_cloud:true,confidential:confidential||!!caseId});setQuery(r.text)}catch(e){onError(e)}finally{setBusy(false)}return
  }
  if(confidential){onError(tr('cloudNote'));return}
  if(!caps?.bhashini.configured){onError(tr('notConfigured'));return}
  if(!window.confirm(tr('voiceConsent')))return
  try{const stream=await navigator.mediaDevices.getUserMedia({audio:true});const context=new AudioContext();const source=context.createMediaStreamSource(stream);const processor=context.createScriptProcessor(4096,1,1);const chunks:Float32Array[]=[];let samples=0;processor.onaudioprocess=e=>{if(samples<context.sampleRate*60){const data=new Float32Array(e.inputBuffer.getChannelData(0));chunks.push(data);samples+=data.length}};source.connect(processor);processor.connect(context.destination);voice.current={context,stream,source,processor,chunks};setRecording(true)}catch(e){onError(e)}
 }
 const examples=[{icon:Leaf,label:'patentLabel',query:'patentQuestion'},{icon:ShieldCheck,label:'absLabel',query:'absQuestion'},{icon:FlaskConical,label:'categoryLabel',query:'categoryQuestion'},{icon:Globe2,label:'exportLabel',query:'exportQuestion'}] as const
 return <section className={`chat-workspace ${turns.length?'has-turns':''}`}>
  {!turns.length&&<div className="welcome"><div className="welcome-emblem"><Leaf size={30} strokeWidth={1.3}/></div><div className="eyebrow">{tr('evidenceFirst')}</div><h1>{tr('welcome')}</h1><p>{tr('welcomeSub')}</p></div>}
  {!!turns.length&&<div className="turns-toolbar"><span className="eyebrow">{tr('assistant')} / {tr(jurisdiction)}</span><Button variant="outline" size="sm" onClick={onSave}><Bookmark size={15}/>{tr('save')}</Button></div>}
  <div className="turns">{turns.map((turn,index)=><article key={turn.answer.trace_id} className="turn"><div className="user-question"><span className="question-number">{String(index+1).padStart(2,'0')}</span><h2>{turn.question}</h2></div><div className="answer"><div className="answer-heading"><span className="small-emblem"><Leaf size={17}/></span><strong>Sahayak</strong><span className={`badge ${turn.answer.evidence_status==='supported'?'green':turn.answer.evidence_status==='partial'?'amber':'neutral'}`}>{tr(turn.answer.evidence_status as Key)}</span><small>{tr(turn.answer.mode as Key)}</small></div><h3>{turn.answer.heading}</h3>{turn.answer.translation&&<div className="translation"><span className="eyebrow">{tr('translation')}</span><p>{turn.answer.translation}</p></div>}{turn.answer.mode==='retrieval'&&<p className="info-box">{tr('excerptNotice')}</p>}<div className="claims">{turn.answer.claims.map((claim,i)=><p key={i} className={turn.answer.mode==='retrieval'?'source-excerpt':undefined}>{claim.kind==='clarification'&&<strong>{tr('clarificationLabel')} </strong>}{claim.text.replace(/\s+/g,' ').trim()} {claim.citation_ids.map(id=><button className="inline-citation" key={id} onClick={()=>{const c=turn.answer.citations.find(c=>c.id===id);if(c)onCitation(c)}} aria-label={tr('viewSource')}>{turn.answer.citations.findIndex(c=>c.id===id)+1}</button>)}</p>)}</div>{!!turn.answer.citations.length&&<div className="answer-sources"><span className="eyebrow">{tr('citations')}</span><div className="source-chips">{turn.answer.citations.map((c,i)=><button key={c.id} onClick={()=>onCitation(c)}><span>{i+1}</span><div><strong>{c.title}</strong><small>{c.locator.slice(0,85)}</small></div><ArrowUpRight size={16}/></button>)}</div></div>}<details className="limitations" open={true}><summary><Info size={15}/>{tr('limitations')}</summary><ul>{turn.answer.limitations.filter(l=>typeof l==='string'&&l.trim()).map((l,i)=><li key={i}>{l}</li>)}</ul></details><div className="answer-actions"><button onClick={()=>feedback(turn.answer,'helpful')}><ThumbsUp size={15}/>{tr('helpful')}</button><button onClick={()=>feedback(turn.answer,'citation')}><Flag size={15}/>{tr('reportIssue')}</button><button onClick={()=>downloadJSON('ipsakti-answer.json',turn.answer)}><Download size={15}/>{tr('export')}</button><button onClick={()=>speak(turn.answer)} disabled={!caps?.bhashini.configured}><Volume2 size={15}/>{tr('listen')}</button><small>{turn.answer.metrics.retrieval} · {Math.round((turn.answer.metrics.elapsed_ms||0)/100)/10}s</small></div></div></article>)}<div ref={end}/></div>
  {busy&&<div className="loading-answer" role="status"><LoaderCircle size={18} className="spin"/>{tr('working')}</div>}
  <form className="composer" onSubmit={e=>{e.preventDefault();void send()}}><textarea aria-label={tr('ask')} placeholder={tr('ask')} value={query} onChange={e=>setQuery(e.target.value)} maxLength={4000} onKeyDown={e=>{if(e.key==='Enter'&&!e.shiftKey&&!e.nativeEvent.isComposing){e.preventDefault();void send()}}}/><div className="composer-bottom"><span><BookOpen size={14}/>{caps?.generation.configured ? caps.generation.model : tr('retrievalOnly')} · {caps?.embeddings.enabled ? tr('semanticSearch') : tr('keywordSearch')}</span><div><button type="button" className={`voice-button ${recording?'recording':''}`} title={tr(recording?'stop':'voice')} aria-label={tr(recording?'stop':'voice')} onClick={record}>{recording?<Square size={18}/>:<Mic size={19}/>}</button><Button disabled={busy||query.trim().length<3} type="submit">{tr('send')}<ArrowUp size={17}/></Button></div></div></form>
  <div className="privacy-controls"><label><input type="checkbox" checked={confidential} onChange={e=>{setConfidential(e.target.checked);if(e.target.checked)setCloud(false)}}/><LockKeyhole size={13}/>{tr('confidential')}</label><label><input type="checkbox" checked={cloud} disabled={confidential} onChange={e=>setCloud(e.target.checked)}/>{tr('cloud')}</label></div>
  {cloud&&<p className="privacy-note">{tr('cloudNote')}</p>}
  {audio&&<audio controls autoPlay src={audio} className="audio-player"/>}
  {!turns.length&&<div className="suggestions"><div className="eyebrow">{tr('suggested')}</div><div className="suggestion-grid">{examples.map(({icon:Icon,label,query:q})=><button key={q} onClick={()=>{if(q==='exportQuestion'&&jurisdiction==='india'){onNotice(tr('scopeNote'));setQuery(tr(q))}else setQuery(tr(q))}}><div><Icon size={20}/><ArrowUpRight size={16}/></div><strong>{tr(label)}</strong><p>{tr(q)}</p></button>)}</div><div className="guided-hint"><FlaskConical size={17}/><span>{tr('classificationSub')}</span><button onClick={()=>onNavigate('classification')}>{tr('classification')}<ChevronRight size={15}/></button></div></div>}
 </section>
}

function AuthDialog({open,onOpenChange,lang,onError,onDone}:{open:boolean;onOpenChange:(v:boolean)=>void;lang:Lang;onError:(e:unknown)=>void;onDone:(user:any)=>void}){
 const [mode,setMode]=useState<'login'|'register'>('login'),[email,setEmail]=useState(''),[password,setPassword]=useState(''),[busy,setBusy]=useState(false)
 const tr=(k:Key)=>t(k,lang)
 async function submit(e:React.FormEvent){e.preventDefault();setBusy(true);try{const result=await post('/auth/'+mode,{email,password});setCSRF(result.csrf_token);setPassword('');onDone(result.user)}catch(e){onError(e)}finally{setBusy(false)}}
 return <Dialog open={open} onOpenChange={onOpenChange}><DialogContent><span className="small-emblem"><Leaf size={23}/></span><DialogTitle>{tr(mode==='login'?'signIn':'register')}</DialogTitle><DialogDescription>{tr('authSub')}</DialogDescription><form onSubmit={submit} className="stack-form"><label>{tr('email')}<input autoComplete="email" type="email" required value={email} onChange={e=>setEmail(e.target.value)}/></label><label>{tr('password')}<input autoComplete={mode==='login'?'current-password':'new-password'} type="password" minLength={12} maxLength={128} required value={password} onChange={e=>setPassword(e.target.value)}/></label><Button disabled={busy}>{busy?<LoaderCircle className="spin" size={18}/>:tr(mode==='login'?'signIn':'register')}</Button><Button type="button" variant="ghost" onClick={()=>setMode(mode==='login'?'register':'login')}>{tr(mode==='login'?'register':'signIn')}<ArrowUpRight size={15}/></Button></form></DialogContent></Dialog>
}

function encodeWav(input:Float32Array,sampleRate:number){
 const rate=16000,ratio=sampleRate/rate,length=Math.min(Math.floor(input.length/ratio),rate*60)
 const buffer=new ArrayBuffer(44+length*2),view=new DataView(buffer)
 const str=(offset:number,value:string)=>{for(let i=0;i<value.length;i++)view.setUint8(offset+i,value.charCodeAt(i))}
 str(0,'RIFF');view.setUint32(4,36+length*2,true);str(8,'WAVE');str(12,'fmt ');view.setUint32(16,16,true);view.setUint16(20,1,true);view.setUint16(22,1,true);view.setUint32(24,rate,true);view.setUint32(28,rate*2,true);view.setUint16(32,2,true);view.setUint16(34,16,true);str(36,'data');view.setUint32(40,length*2,true)
 for(let i=0;i<length;i++){const s=Math.max(-1,Math.min(1,input[Math.floor(i*ratio)]));view.setInt16(44+i*2,s<0?s*32768:s*32767,true)}return buffer
}
