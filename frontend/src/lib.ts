import type {components} from './generated/api'
import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'
export function cn(...inputs: ClassValue[]) { return twMerge(clsx(inputs)) }
let csrf = ''
export function setCSRF(value: string) { csrf = value }
export async function api<T=any>(path:string, options:RequestInit={}):Promise<T> {
  const headers:Record<string,string> = {'X-CSRF-Token':csrf}
  if (!(options.body instanceof FormData)) headers['Content-Type']='application/json'
  const response=await fetch('/api/v1'+path,{...options,credentials:'include',headers:{...headers,...options.headers}})
  if (!response.ok) {
    const raw=await response.text()
    let message=raw
    try { const data=JSON.parse(raw); message=typeof data.detail==='string'?data.detail:JSON.stringify(data.detail) } catch { /* plain gateway error */ }
    throw new Error(message || `Request failed (${response.status})`)
  }
  return response.json()
}
export function post<T=any>(path:string,body:unknown){return api<T>(path,{method:'POST',body:JSON.stringify(body)})}
export function downloadJSON(name:string,data:unknown){
  const url=URL.createObjectURL(new Blob([JSON.stringify(data,null,2)],{type:'application/json'}))
  const a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),500)
}
export type Lang='en'|'hi'|'mr'
export type Jurisdiction='india'|'international'
export type Market='treaties'|'us'|'eu'|'uk'
export type Citation=components['schemas']['Citation']&{file_url?:string;checksum?:string;review_note?:string}
export type Answer={trace_id:string;mode:string;heading:string;claims:{kind?:'explanation'|'clarification';text:string;citation_ids:string[];support_quote:string}[];citations:Citation[];evidence_status:string;limitations:string[];next_steps:string[];disclaimer:string;translation:string|null;metrics:{elapsed_ms?:number;retrieval?:string};jurisdiction:Jurisdiction;market:Market}
export type Turn={question:string;answer:Answer}
