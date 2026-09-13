import { TaskList } from './TaskList'
import { RunPreparation } from './RunPreparation'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { createRoot, type Root } from 'react-dom/client'
import { GenerationControls } from './GenerationControls'
const flush=()=>new Promise(r=>setTimeout(r,30))
let root:Root|undefined;let host:HTMLDivElement|undefined
const original=globalThis.fetch
afterEach(()=>{root?.unmount();host?.remove();globalThis.fetch=original})
const refs={context_package_id:'cp-fixed',requirements_ref:'sha256:req',validation_ref:'sha256:val',baseline_ref:'sha256:base',input_ref:'sha256:captured'}
const generation={task_id:'t',revision:1,control_revision:0,closed:0,aborted:0,ownership_unknown:0,inputs:refs,writer:null,workspace:null,events:[]}
async function mount(onSelected=vi.fn()) {host=document.createElement('div');document.body.append(host);root=createRoot(host);root.render(<GenerationControls config={{baseUrl:'/api/v1',getAuthHeaders:()=>({})}} taskId="t" contextId="cp-fixed" onSelected={onSelected}/>);await flush();return onSelected}
function button(label:string){return Array.from(host!.querySelectorAll('button')).find(b=>b.textContent===label)!}
function fill(label:string,value:string){const field=Array.from(host!.querySelectorAll('label')).find(e=>e.textContent?.startsWith(label))!.querySelector('textarea')!;Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype,'value')!.set!.call(field,value);field.dispatchEvent(new Event('input',{bubbles:true}))}
describe('explicit generation workflow',()=>{
 it('does not select latest or begin automatically, and uses fixed server refs',async()=>{
  const calls:Array<{url:string;method:string;body:any}>=[];let begun=false
  globalThis.fetch=vi.fn(async(input,init)=>{const url=String(input),method=init?.method??'GET',body=init?.body?JSON.parse(String(init.body)):undefined;calls.push({url,method,body});let data:unknown
   if(url.endsWith('/inputs'))data=refs
   else if(method==='POST'){begun=true;data={generation_revision:1}}
   else if(url.endsWith('/generations/1'))data=generation
   else data={task_revision:begun?1:0,generations:begun?[generation]:[]}
   return new Response(JSON.stringify(data),{status:method==='POST'?201:200})}) as typeof fetch
  const selected=await mount();expect(calls).toHaveLength(0)
  button('Load generations').focus();expect(document.activeElement).toBe(button('Load generations'));button('Load generations').click();await flush()
  expect(selected).not.toHaveBeenCalled();expect(button('Begin work').disabled).toBe(true)
  fill('Requirements','Clear requirements');fill('Validation criteria','Check the result');await flush();button('Prepare inputs').click();await flush()
  expect(calls.some(c=>c.method==='POST'&&c.url.endsWith('/generations'))).toBe(false)
  button('Begin work').click();await flush();await flush()
  const begin=calls.find(c=>c.method==='POST'&&c.url.endsWith('/generations'))!
  expect(begin.body.inputs).toEqual(refs);expect(begin.body.expected_revision).toBe(0);expect(begin.body.command_id).toBeTruthy()
  expect(selected).toHaveBeenLastCalledWith(generation);expect(calls.some(c=>c.url.includes('/runs'))).toBe(false)
 })
 it('keeps unknown ownership fail-closed and exposes refresh errors',async()=>{
  globalThis.fetch=vi.fn(async()=>new Response(JSON.stringify({task_revision:1,generations:[{...generation,ownership_unknown:1}]}))) as typeof fetch
  const selected=await mount();button('Load generations').click();await flush();(host!.querySelector('input[name="generation"]') as HTMLInputElement).click();await flush()
  expect(button('Abort selected generation').disabled).toBe(true);expect(button('Begin work').disabled).toBe(true)
  globalThis.fetch=vi.fn(async()=>{throw new Error('offline')}) as typeof fetch
  button('Load generations').click();await flush();expect(host!.querySelector('[role="alert"]')).not.toBeNull();expect(selected).toHaveBeenLastCalledWith(null)
 })
})

 it('preserves abort observations and ignores an older failed refresh',async()=>{
  const response=(aborted:number)=>new Response(JSON.stringify({task_revision:1,generations:[{...generation,aborted}]}))
  globalThis.fetch=vi.fn(async()=>response(1)) as typeof fetch
  const selected=await mount();button('Load generations').click();await flush();(host!.querySelector('input[name="generation"]') as HTMLInputElement).click();await flush()
  let rejectOld!:(reason:Error)=>void
  globalThis.fetch=vi.fn(()=>new Promise<Response>((_resolve,reject)=>{rejectOld=reject})) as typeof fetch
  button('Load generations').click();await flush()
  globalThis.fetch=vi.fn(async()=>response(0)) as typeof fetch
  button('Load generations').click();await flush()
  expect(button('Abort selected generation').disabled).toBe(true)
  expect(selected).toHaveBeenLastCalledWith({...generation,aborted:1})
  rejectOld(new Error('older request offline'));await flush()
  expect(host!.querySelector('[role="alert"]')).toBeNull()
  expect(selected).toHaveBeenLastCalledWith({...generation,aborted:1})
 })

 it('reconnects with the durable cursor and retains exact terminal selection on unchanged',async()=>{
  const calls:string[]=[];let unchanged=false
  globalThis.fetch=vi.fn(async(input,init)=>{calls.push(String(input));expect(init?.method).toBe('GET');return new Response(JSON.stringify({task_revision:1,cursor:'server-cursor',unchanged,generations:[{...generation,closed:1}]}))}) as typeof fetch
  const selected=await mount();button('Load generations').click();await flush();(host!.querySelector('input[name="generation"]') as HTMLInputElement).click();await flush()
  expect(button('Abort selected generation').disabled).toBe(true)
  unchanged=true;window.dispatchEvent(new Event('online'));await flush()
  expect(calls.at(-1)).toContain('?cursor=server-cursor')
  expect((host!.querySelector('input[name="generation"]') as HTMLInputElement).checked).toBe(true)
  expect(selected).toHaveBeenLastCalledWith({...generation,closed:1})
  expect(button('Abort selected generation').disabled).toBe(true)
  expect(calls).toHaveLength(2)
 })

 it('keeps all three archived task entries readable and blocks new work without blocking Abort',async()=>{
  const tasks=['DISCUSS','REVIEW','VALIDATE'].map((mode,n)=>({id:'t'+n,project_id:'p',title:mode,mode,workflow_id:'review-minimal',workflow_version:1,context_package_id:'cp-fixed',created_at:'2026-01-01T00:00:00Z'}))
  const calls:Array<{url:string;method:string}>=[]
  globalThis.fetch=vi.fn(async(input,init)=>{const url=String(input);calls.push({url,method:init?.method??'GET'});return new Response(JSON.stringify(url.endsWith('/tasks')?{tasks}:url.includes('/generations')?{task_revision:1,generations:[generation]}:{runs:[]}))}) as typeof fetch
  host=document.createElement('div');document.body.append(host);root=createRoot(host)
  const config={baseUrl:'/api/v1',getAuthHeaders:()=>({})};const select=vi.fn()
  root.render(<TaskList config={config} projectId="p" archived onSelectTask={select} onBack={()=>{}}/>);await flush()
  expect(button('New task').disabled).toBe(true)
  const entries=host.querySelectorAll<HTMLButtonElement>('.task-item-btn');expect(entries).toHaveLength(3)
  entries.forEach(entry=>entry.click());expect(select.mock.calls.map(call=>call[0].mode)).toEqual(['DISCUSS','REVIEW','VALIDATE'])
  root.render(<RunPreparation config={config} task={tasks[1]} archived onBack={()=>{}} onOpenDetail={()=>{}}/>);await flush()
  expect(button('Create Run').disabled).toBe(true)
  expect(button('+ Create new ContextPackage').disabled).toBe(true)
  expect((host.querySelector('input[type="file"]') as HTMLInputElement).disabled).toBe(true)
  expect(button('Prepare inputs').closest('fieldset')!.disabled).toBe(true)
  button('Load generations').click();await flush();(host.querySelector('input[name="generation"]') as HTMLInputElement).click();await flush()
  expect(button('Abort selected generation').disabled).toBe(false)
  expect(button('Begin work').disabled).toBe(true)
  expect(button('Create Run').disabled).toBe(true)
  expect(calls.every(call=>call.method==='GET')).toBe(true)
 })
