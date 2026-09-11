import type {components} from './generated/api'
import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'
export function cn(...inputs: ClassValue[]) { return twMerge(clsx(inputs)) }
let csrf = ''
let sessionPromise: Promise<any> | null = null
export function setCSRF(value: string) { csrf = value }
async function request<T=any>(path:string, options:RequestInit={}):Promise<T> {
  const headers = new Headers(options.headers)
  headers.set('X-CSRF-Token', csrf)
  if (!(options.body instanceof FormData)) headers.set('Content-Type','application/json')
  const response=await fetch('/api/v1'+path,{...options,credentials:'include',headers})
  if (!response.ok) {
    const raw=await response.text()
    let message=raw
    try { const data=JSON.parse(raw); message=typeof data.detail==='string'?data.detail:JSON.stringify(data.detail) } catch { /* plain gateway error */ }
    throw new Error(message || `Request failed (${response.status})`)
  }
  const data = response.status === 204 ? null : await response.json()
  if (data?.csrf_token) csrf = data.csrf_token
  return data as T
}
// All callers share one bootstrap, including React StrictMode and mount effects.
export function ensureSession(): Promise<any> {
  if (!sessionPromise) {
    sessionPromise = request('/auth/session').catch(error => {
      sessionPromise = null
      csrf = ''
      throw error
    })
  }
  return sessionPromise
}
export async function api<T=any>(path:string, options:RequestInit={}):Promise<T> {
  if (path === '/auth/session') return ensureSession() as Promise<T>
  if (!['GET','HEAD','OPTIONS'].includes((options.method || 'GET').toUpperCase())) {
    await ensureSession()
  }
  const result = await request<T>(path, options)
  if (['/auth/logout','/account'].includes(path) && (options.method || 'GET') !== 'GET') {
    csrf = ''
    sessionPromise = null
  }
  return result
}
export function post<T=any>(path:string,body:unknown){return api<T>(path,{method:'POST',body:JSON.stringify(body)})}
export async function streamQuestion(body:components['schemas']['Question'], onStage:(stage:string)=>void, signal?:AbortSignal):Promise<Answer> {
  await ensureSession()
  const response = await fetch('/api/v1/questions/stream', {
    method:'POST', credentials:'include', signal,
    headers:{'Content-Type':'application/json','X-CSRF-Token':csrf}, body:JSON.stringify(body)
  })
  if (!response.ok) throw new Error(await response.text() || `Request failed (${response.status})`)
  if (!response.body) throw new Error('Streaming is unavailable')
  const reader=response.body.getReader(), decoder=new TextDecoder()
  let buffer='', answer:Answer|null=null
  function consume(frame:string) {
    const lines=frame.split('\n'), event=lines.find(line=>line.startsWith('event:'))?.slice(6).trim()
    const raw=lines.filter(line=>line.startsWith('data:')).map(line=>line.slice(5).trimStart()).join('\n')
    if (!raw) return
    const data=JSON.parse(raw)
    if (event==='stage'||event==='progress') onStage(data.stage)
    if (event==='answer') answer=data
    if (event==='error') throw new Error(data.message || 'Question processing failed')
  }
  try {
    while (true) {
      const {value,done}=await reader.read()
      buffer+=decoder.decode(value,{stream:!done})
      // This server emits LF; normalize CRLF after complete line boundaries.
      buffer=buffer.replace(/\r\n/g,'\n')
      let boundary:number
      while ((boundary=buffer.indexOf('\n\n'))>=0) {
        consume(buffer.slice(0,boundary)); buffer=buffer.slice(boundary+2)
      }
      if (done) break
    }
    if (buffer.trim()) consume(buffer)
    if (!answer) throw new Error('Stream ended without an answer')
    return answer
  } finally { await reader.cancel(); reader.releaseLock() }
}
export function downloadJSON(name:string,data:unknown){
  const url=URL.createObjectURL(new Blob([JSON.stringify(data,null,2)],{type:'application/json'}))
  const a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),500)
}
export type Lang='en'|'hi'|'mr'
export type Jurisdiction='india'|'international'
export type Market='treaties'|'us'|'eu'|'uk'
export type Citation=components['schemas']['Citation']&{file_url?:string;checksum?:string;review_note?:string;heading?:string;support_quote?:string}
export type Answer={trace_id:string;mode:string;heading:string;claims:{kind?:'explanation'|'clarification';text:string;citation_ids:string[];support_quote:string}[];citations:Citation[];evidence_status:string;limitations:string[];next_steps:string[];disclaimer:string;translation:string|null;metrics:{elapsed_ms?:number;retrieval?:string};jurisdiction:Jurisdiction;market:Market}
export type Turn={question:string;answer:Answer}
