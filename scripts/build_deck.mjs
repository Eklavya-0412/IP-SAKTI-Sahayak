import fs from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import {Presentation,PresentationFile} from '@oai/artifact-tool';
process.env.RUNTIME_NODE_MODULES='C:/Users/Rushabh/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules';
const ROOT=path.resolve(import.meta.dirname,'../..');
const SKILL='C:/Users/Rushabh/.codex/plugins/cache/openai-primary-runtime/presentations/26.904.11930/skills/presentations';
const PYTHON='C:/Users/Rushabh/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe';
const {finalizePresentation,resolvePresentationFont}=await import(pathToFileURL(path.join(SKILL,'container_tools/artifact_tool_utils.mjs')).href);
const font=resolvePresentationFont({fontFamily:'Segoe UI',availableFonts:['Segoe UI']});
const metrics=JSON.parse(await fs.readFile(path.join(ROOT,'docs/submission-metrics.json'),'utf8'));
const p=Presentation.create({slideSize:{width:1280,height:720}});
const C={green:'#234335',cream:'#F6F4ED',gold:'#B77934',ink:'#25332C',muted:'#627066',line:'#D5DBD0',white:'#FFFFFF'};
function text(slide,value,x,y,w,h,size=28,color=C.ink,bold=false){const s=slide.shapes.add({geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});s.text=value;s.text.style={typeface:font,fontSize:size,color,bold,autoFit:'none'};return s;}
function rect(slide,x,y,w,h,fill=C.cream){return slide.shapes.add({geometry:'rect',position:{left:x,top:y,width:w,height:h},fill,line:{fill:'none',width:0}})}
function slide(title,note='Implementation evidence: docs/PROJECT_REPORT.md; corpus/inventory.json; docs/EVALUATION.md.'){const s=p.slides.add();s.background.fill=C.cream;text(s,title,64,48,1152,105,44,C.green,true);text(s,String(p.slides.items.length).padStart(2,'0'),1160,660,50,24,14,C.muted);s.speakerNotes.textFrame.setText(note);return s;}
function row(s,left,right,y){text(s,left,66,y,330,64,27,C.green,true);text(s,right,420,y,780,92,25,C.ink);}
function table(s,values,y=200){const t=s.tables.add({rows:values.length,columns:values[0].length,left:65,top:y,width:1150,height:values.length*64,values});for(let r=0;r<values.length;r++)for(let c=0;c<values[0].length;c++){const cell=t.getCell(r,c);cell.fill=r===0?C.green:(r%2?C.white:C.cream);cell.text.style={typeface:font,fontSize:21,bold:r===0,color:r===0?C.white:C.ink};}return t;}
function chain(s,labels,y=250){const gap=40,w=(1150-gap*(labels.length-1))/labels.length;labels.forEach((label,i)=>{const x=65+i*(w+gap);rect(s,x,y,w,112,C.white);text(s,label,x+16,y+25,w-32,72,25,C.green,true);if(i<labels.length-1)text(s,'→',x+w,y+30,40,40,22,C.gold)});}

{
const s=slide('IP-SAKTI\nSahayak','Project submission, 6 September 2026. All counts are drawn from docs/submission-metrics.json. No legal advice, certification or public launch is claimed.');
s.background.fill=C.green;s.shapes.items[0].text.style={typeface:font,fontSize:64,color:C.cream,bold:true,autoFit:'none'};s.shapes.items[0].position={left:64,top:48,width:1152,height:175};
text(s,'Ayurveda innovation,\ngrounded in inspectable sources.',66,250,1000,120,40,C.cream);
text(s,'Deployable multilingual pilot · India + international regimes',68,418,1120,55,25,'#D9E4D6');
text(s,`${metrics.sources_registered} registered sources    /    3 interface languages    /    381 evaluation executions`,68,534,1100,54,24,'#E5BA7D');
text(s,'Information, not legal advice. Expert legal and language review remain release gates.',68,632,1080,40,18,'#D9E4D6');
}
{
const s=slide('One formulation raises three connected questions');
row(s,'What is the product?','Medicine, food, phytopharmaceutical or cosmetic: classification determines which regulatory route to investigate.',190);
row(s,'What can be protected?','Patents, brands, designs, geographical indications, copyright, trade secrets and plant varieties need distinct evidence.',335);
row(s,'How was it accessed?','Biological resources and associated traditional knowledge create a separate ABS assessment.',480);
}
{
const s=slide('The working assistant starts with scope');
chain(s,['India or international','Treaties / US / EU / UK','English / Hindi / Marathi'],205);
text(s,'Ask a question → inspect citations → save a case → request selected review',68,392,1120,85,33,C.green,true);
text(s,'Each jurisdiction has a separate answer history. Source excerpts remain labelled when generation or translation is unavailable.',68,523,1110,100,27);
}
{
const s=slide('Source acquisition is separate from legal approval');
table(s,[['Evidence layer','Observed state'],['Supplied originals',`${metrics.original_pdfs} PDFs preserved and checksummed`],['Registered source candidates',String(metrics.sources_registered)],['Acquired source versions',String(metrics.source_versions)],['Active reference chunks',String(metrics.active_chunks)],['Approved current-law versions',`${metrics.approved_versions} — qualified review pending`]],170);
}
{
const s=slide('A citation has a reproducible path');
chain(s,['Official source','SHA-256 snapshot','Page / section chunk','Returned citation'],220);
text(s,'Publisher • URL • retrieval date • effective date • authority class • review status',68,413,1130,80,27,C.green,true);
text(s,'Drafts, forms, notices and statistics remain distinct. Unretrieved or empty documents cannot support an answer.',68,532,1120,85,27);
}
{
const s=slide('Bounded retrieval and verification');
chain(s,['Scope + privacy','Hybrid retrieval','Evidence graph','Draft / excerpts'],194);
chain(s,['Citation IDs','Exact support quote','Entailment check','Release or abstain'],378);
text(s,'No unrestricted model tools. No invented URLs. An automated judge is still subject to expert evaluation.',68,571,1120,65,24,C.muted);
}
{
const s=slide('Classification stays provisional');
table(s,[['Product facts','Route to investigate'],['Authoritative text + unchanged method','Classical ASU medicine'],['Qualifying ingredients; modified formulation','Patent-or-proprietary ASU medicine'],['Other / standardized fraction','New-drug or phytopharmaceutical assessment'],['Food intent / appearance claims','Ayurveda-Aahara, food or cosmetic route']],181);
text(s,'A regulatory category is neither a patent grant nor a patentability opinion. Ambiguous facts trigger clarification.',68,560,1120,78,26,C.green,true);
}
{
const s=slide('ABS and prior art are separate workspaces');
row(s,'ABS checklist','Applicant control, resource origin, purpose, research transfer, IP stage, cultivation and associated TK.',188);
row(s,'Evidence to collect','Procurement and origin records, relevant state, access dates, documentary conditions and unresolved exemptions.',330);
row(s,'Lawful navigation','Botanical/common-name search terms, official registry links and TKDL access pointers. No paywall or CAPTCHA bypass.',472);
}
{
const s=slide('Private cases stay behind explicit boundaries');
chain(s,['Signed-in owner','Private case / files','Selected submission','Facilitator queue'],212);
text(s,'Free hosted generation: general questions + public sources + explicit opt-in.',70,402,1110,72,29,C.green,true);
text(s,'Private context: local inference only. Reviewers receive the content selected for submission. Consent can be inspected and revoked.',70,507,1100,110,27);
}
{
const s=slide('Multilingual and voice availability is visible');
table(s,[['Experience','Implemented boundary'],['English / Hindi / Marathi','Interface and guided questions; original legal excerpts retained'],['Translation / speech recognition / speech synthesis','Configurable Bhashini adapter; credentials required'],['Voice questions','User reviews the transcript before submitting'],['Translation verification','Numeric/reference checks; expert meaning review pending']],185);
text(s,'No prerecorded or sample output is represented as a live provider response.',70,570,1110,60,25,C.green,true);
}
{
const s=slide('Docker deployment and recovery were exercised');
chain(s,['Nginx web','FastAPI','PostgreSQL + pgvector','Persistent volumes'],190);
text(s,'Separate migration and worker containers',70,357,1120,60,32,C.green,true);
text(s,`Rehearsal: ${metrics.deployment.status}. ${metrics.deployment.document_checksums_verified??0} archived source files verified; database restored into an isolated test database.`,70,447,1120,108,28);
text(s,'Production TLS, encrypted storage, scheduled backups and staffing are deployment-owner responsibilities.',70,590,1100,58,22,C.muted);
}
{
const s=slide('Measured traceability; legal accuracy is unmeasured','Actual results: evals/results/latest.json and docs/test-results.xml. Scores include vacuous citation-mechanics passes for abstentions. Four adversarial scenarios per language are not a comprehensive safety sample.');
const rows=[['Language','Executions','Citation resolution','p50 / p95 ms']];
for(const [lang,r] of Object.entries(metrics.evaluation))rows.push([lang.toUpperCase(),String(r.n),`${Math.round(r.citation_resolution*100)}%`,`${Math.round(r.p50_ms)} / ${Math.round(r.p95_ms)}`]);
table(s,rows,179);
text(s,`${metrics.backend_tests.tests??'—'} backend tests passed. No qualified legal or language scores are claimed.`,70,480,1120,82,30,C.green,true);
text(s,'These sequential source-only timings do not predict hosted generation or voice latency.',70,592,1120,53,22,C.muted);
}
{
const s=slide('Release gates remain explicit');
row(s,'Qualified review','Current-law applicability, missing amendments, classification logic, citation relevance and language quality.',184);
row(s,'Credentials and models','Gemini/Ollama evaluation, Bhashini service tests and any licensed paid-source connector.',328);
row(s,'Production readiness','Authentication hardening, privacy/legal assessment, TLS/storage, incident procedures and facilitator staffing.',472);
}
{
const s=slide('A reviewable pilot and a reproducible submission');
text(s,'Source code + migrations + Docker\nCorpus manifest + inventory + coverage\nAPI contract + tests + evaluation data\nReport + guides + diagrams + demo script',70,186,1120,282,36,C.green,true);
text(s,'Next: approve the evidence, validate providers, and measure expert-reviewed answer quality before public operation.',70,529,1100,107,29);
}
await fs.mkdir(path.join(ROOT,'deliverables'),{recursive:true});
const candidate=path.join(import.meta.dirname,'candidate.pptx');
await(await PresentationFile.exportPptx(p)).save(candidate);
await fs.mkdir(path.join(import.meta.dirname,'renders'),{recursive:true});
for(let i=0;i<p.slides.items.length;i++){
 const image=await p.export({slide:p.slides.items[i],format:'png',scale:1});
 await fs.writeFile(path.join(import.meta.dirname,'renders',`slide-${i+1}.png`),new Uint8Array(await image.arrayBuffer()));
}
const result=await finalizePresentation({workspaceDir:ROOT,candidatePath:candidate,finalPath:path.join(ROOT,'deliverables/IP-SAKTI-Submission-20260906.pptx'),
 pythonExecutable:PYTHON,integrityValidatorPath:path.join(SKILL,'container_tools/inspect_presentation_package_integrity.py'),layoutValidatorPath:path.join(SKILL,'container_tools/inspect_presentation_layout_geometry.py'),
 layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-heading-fit',...([4,7,10,12].flatMap(i=>['--require-native-table-slide',String(i)]))],explicitTotalSlideCount:14,requiredNativeTableOwnerSlides:[4,7,10,12],
 fontPolicy:{basis:'design',families:[font]},verifyArtifactToolImport:true,receiptPath:path.join(import.meta.dirname,'validation-20260906.json')});
console.log(JSON.stringify(result,null,2));
