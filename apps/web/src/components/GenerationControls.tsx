import { useCallback, useEffect, useRef, useState } from 'react'
import type { ApiClientConfig, Generation } from '../api'
import { workRequest, taskGenerationPath, ApiError } from '../api'

interface Props { archived?: boolean; config: ApiClientConfig; taskId: string; contextId: string; onSelected: (generation: Generation | null) => void }
export function GenerationControls({config, taskId, contextId, onSelected, archived=false}: Props) {
  const [items,setItems]=useState<Generation[]>([]), [revision,setRevision]=useState<number|null>(null)
  const [chosen,setChosen]=useState<number|null>(null), [busy,setBusy]=useState(false), [error,setError]=useState('')
  const [requirements,setRequirements]=useState(''), [validation,setValidation]=useState(''), [repository,setRepository]=useState('')
  const [baseline,setBaseline]=useState<string|null>(null), [dirty,setDirty]=useState<string[]>([]), [selected,setSelected]=useState<string[]>([])
  const [mode,setMode]=useState('STANDARD'), [secretRef,setSecretRef]=useState(''), [prepared,setPrepared]=useState<Record<string,string>|null>(null)
  const [retry,setRetry]=useState(false), [notice,setNotice]=useState('')
  const section=useRef<HTMLElement>(null), selection=useRef<number|null>(null), callback=useRef(onSelected)
  callback.current=onSelected
  const commands=useRef(new Map<string,string>())
  const observed=useRef(new Map<number,Generation>()), sequence=useRef(0), durableCursor=useRef<string|null>(null)
  const command=(kind:string,payload:unknown) => { const key=kind+JSON.stringify(payload); let id=commands.current.get(key); if(!id){id=crypto.randomUUID();commands.current.set(key,id)} return id }
  const choose=(generation:Generation|null) => { selection.current=generation?.revision??null;setChosen(selection.current);callback.current(generation) }
  const load=useCallback(async () => {
    const requestSequence=++sequence.current
    try {
      const data=await workRequest<{task_revision:number;generations:Generation[];cursor?:string;unchanged?:boolean}>(config,'GET',taskGenerationPath(taskId)+(durableCursor.current?'?cursor='+encodeURIComponent(durableCursor.current):''))
      if(!Array.isArray(data.generations)) throw new Error('Invalid response')
      if(requestSequence!==sequence.current)return
      durableCursor.current=data.cursor??null
      if(data.unchanged){setError('');if(selection.current!==null)callback.current(observed.current.get(selection.current)??null);return}
      data.generations=data.generations.map(g=>{const old=observed.current.get(g.revision);const value=old&&(old.control_revision>g.control_revision||old.control_revision===g.control_revision&&(!!old.aborted&&!g.aborted||!!old.closed&&!g.closed||!!old.ownership_unknown&&!g.ownership_unknown))?old:g;observed.current.set(g.revision,value);return value})
      setItems(data.generations);setRevision(data.task_revision);setError('')
      if(selection.current!==null) callback.current(data.generations.find(g=>g.revision===selection.current)??null)
    } catch { if(requestSequence!==sequence.current)return;setError('Unable to refresh work. Reconnect and reload before sending commands.');callback.current(null) }
  },[config,taskId])
  useEffect(()=>{setPrepared(null)},[contextId,requirements,validation,repository,baseline,selected,mode,secretRef])
  useEffect(()=>{
    if(revision===null)return
    const timer=window.setInterval(()=>{if(section.current?.isConnected)void load()},5000)
    const reconnect=()=>{if(section.current?.isConnected)void load()}
    window.addEventListener('online',reconnect)
    return()=>{clearInterval(timer);window.removeEventListener('online',reconnect)}
  },[load,revision])
  const act=async (action:()=>Promise<void>)=>{setBusy(true);setError('');try{await action()}catch(e){setError(e instanceof ApiError&&e.status===409?'Work changed or is not safely available. Reload and review the selected generation.':'Unable to complete this action. Check the connection and inputs.')}finally{setBusy(false)}}
  const generation=items.find(g=>g.revision===chosen)
  const canBegin=!archived&&revision!==null&&prepared!==null&&!busy&&!error&&(!items.some(g=>!g.closed||g.ownership_unknown))
  return <section ref={section} className="generation-controls" aria-label="Work generations">
    <h3>Work generations</h3>
    <button type="button" onClick={()=>void load()} disabled={busy}>Load generations</button>
    {error&&<p role="alert">{error}</p>}{notice&&<p role="status" tabIndex={-1}>{notice}</p>}
    {revision!==null&&items.length===0&&<p>No generations yet. Prepare inputs, then explicitly begin work.</p>}
    <fieldset disabled={busy}><legend>Select an exact generation</legend>
      {items.map(g=><label key={g.revision}><input type="radio" name="generation" value={g.revision} checked={chosen===g.revision} onChange={()=>choose(g)}/>
        Generation {g.revision} · {g.ownership_unknown?'Ownership unknown':g.closed?'Closed':g.aborted?'Abort requested':'Open'} · control {g.control_revision}
      </label>)}
    </fieldset>
    <fieldset disabled={busy||archived}><legend>Prepare a new generation</legend>
      <p>Selected ContextPackage ID: {contextId||'Choose or create a context below.'}</p>
      <label>Requirements<textarea value={requirements} onChange={e=>setRequirements(e.target.value)} required/></label>
      <label>Validation criteria<textarea value={validation} onChange={e=>setValidation(e.target.value)} required/></label>
      <label>Execution mode<select value={mode} onChange={e=>setMode(e.target.value)}><option>STANDARD</option><option>LOCAL_PREFERRED</option><option>LOCAL_ONLY</option></select></label>
      <label>SecretRef (optional)<input value={secretRef} onChange={e=>setSecretRef(e.target.value)} placeholder="Dedicated store reference only"/></label>
      <label>Repository relative to configured source root (optional)<input value={repository} onChange={e=>{setRepository(e.target.value);setBaseline(null);setDirty([]);setSelected([])}}/></label>
      <button type="button" disabled={!repository} onClick={()=>void act(async()=>{const data=await workRequest<{baseline_commit:string;dirty_paths:string[]}>(config,'POST','/repositories/inspect',{repository});setBaseline(data.baseline_commit);setDirty(data.dirty_paths);setSelected([])})}>Inspect repository</button>
      {baseline&&<p>Baseline: <code>{baseline}</code></p>}
      {dirty.map(path=><label key={path}><input type="checkbox" checked={selected.includes(path)} onChange={e=>setSelected(old=>e.target.checked?[...old,path]:old.filter(p=>p!==path))}/>{path}</label>)}
      <p>Only checked dirty paths are included. The original repository stays unchanged.</p>
      <button type="button" disabled={!contextId||!requirements.trim()||!validation.trim()||!!repository&&!baseline} onClick={()=>void act(async()=>{const value=await workRequest<Record<string,string>>(config,'POST',`/tasks/${encodeURIComponent(taskId)}/inputs`,{context_package_id:contextId,requirements,validation,execution_mode:mode,repository:repository||null,baseline,selected,secret_ref:secretRef||null});setPrepared(value);setNotice('Inputs captured. Review the fixed references before beginning.')})}>Prepare inputs</button>
      {prepared&&<details open><summary>Fixed input references</summary><pre>{JSON.stringify(prepared,null,2)}</pre></details>}
      <label><input type="checkbox" checked={retry} onChange={e=>setRetry(e.target.checked)}/>Retry selected closed generation</label>
      <button type="button" disabled={!canBegin||retry&&(!generation?.closed||generation.revision!==revision)} onClick={()=>void act(async()=>{const payload={expected_revision:revision,inputs:prepared,predecessor:retry?chosen:null};const accepted=await workRequest<{generation_revision:number}>(config,'POST',taskGenerationPath(taskId),{...payload,command_id:command('begin',payload)});await load();const exact=await workRequest<Generation>(config,'GET',`${taskGenerationPath(taskId)}/${accepted.generation_revision}`);choose(exact);setPrepared(null);setNotice(`Generation ${accepted.generation_revision} created. Create a Run explicitly when ready.`)})}>{retry?'Retry work':'Begin work'}</button>
    </fieldset>
    {generation&&<><h4>Selected generation {generation.revision}</h4><p>Ownership: {generation.workspace?.ownership.state??(generation.writer?'Claimed':'Unclaimed')} · recovery: {generation.workspace?.recoverability.state??'Not materialized'}</p>
      <p>Git: {generation.workspace?.git_observation.state??'Not observed'} · fence: {generation.writer?.fence??'None'}</p>
      <button type="button" disabled={busy||!!error||!!generation.closed||!!generation.ownership_unknown||!!generation.aborted} onClick={()=>void act(async()=>{const payload={expected_control:generation.control_revision};await workRequest(config,'POST',`${taskGenerationPath(taskId)}/${generation.revision}/abort`,{...payload,command_id:command('abort-'+generation.revision,payload)});await load()})}>Abort selected generation</button>
      <details><summary>Durable generation history</summary><ul>{generation.events.map(e=><li key={e.event_id}>{e.kind} · control {e.control_revision}</li>)}</ul></details></>}
  </section>
}
