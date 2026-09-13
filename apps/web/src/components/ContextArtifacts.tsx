import { useState } from 'react'
import type { ApiClientConfig, ContextPackage, Artifact } from '../api'
import { workRequest } from '../api'
export function ContextArtifacts({config,projectId,onSelect,onArtifact,archived=false}:{archived?:boolean;config:ApiClientConfig;projectId:string;onSelect:(id:string)=>void;onArtifact:(id:string)=>void}) {
  const [contexts,setContexts]=useState<ContextPackage[]>([]),[artifacts,setArtifacts]=useState<Artifact[]>([]),[error,setError]=useState(''),[busy,setBusy]=useState(false)
  const [classification,setClassification]=useState('INTERNAL')
  const load=async()=>{setBusy(true);try{const [c,a]=await Promise.all([workRequest<{context_packages:ContextPackage[]}>(config,'GET',`/projects/${encodeURIComponent(projectId)}/context-packages`),workRequest<{artifacts:Artifact[]}>(config,'GET',`/projects/${encodeURIComponent(projectId)}/artifacts`)]);setContexts(c.context_packages);setArtifacts(a.artifacts);setError('')}catch{setError('Unable to load context and artifacts.')}finally{setBusy(false)}}
  const upload=async(file:File)=>{if(archived)return;setBusy(true);setError('');try{if(file.size>16*1024*1024)throw new Error('size');const encoded=await new Promise<string>((resolve,reject)=>{const reader=new FileReader();reader.onerror=reject;reader.onload=()=>resolve(String(reader.result).split(',')[1]);reader.readAsDataURL(file)});const artifact=await workRequest<Artifact>(config,'POST',`/projects/${encodeURIComponent(projectId)}/artifacts`,{content_base64:encoded,mime_type:file.type||'application/octet-stream',classification});onArtifact(artifact.id);await load()}catch{setError('Upload failed. Use a file no larger than 16 MiB.')}finally{setBusy(false)}}
  return <section className="context-artifacts" aria-label="Context versions and artifacts"><h3>Context and immutable artifacts</h3>
    <button type="button" onClick={()=>void load()} disabled={busy}>Load context and artifacts</button>{busy&&<p role="status">Loading content…</p>}{error&&<p role="alert">{error}</p>}
    <ul>{contexts.map(c=><li key={c.id}><button type="button" onClick={()=>onSelect(c.id)}>Use context v{c.version}: {c.id}</button> · {c.classification??'INTERNAL'}</li>)}</ul>
    <label>Upload classification<select value={classification} onChange={e=>setClassification(e.target.value)}>{['PUBLIC','INTERNAL','CONFIDENTIAL','RESTRICTED'].map(c=><option key={c}>{c}</option>)}</select></label>
    <label>Upload artifact<input type="file" disabled={busy||archived} onChange={e=>{const file=e.target.files?.[0];if(file)void upload(file)}}/></label>
    <p>Uploaded content is immutable and retained. Add its reference to a new context version.</p>
    <ul>{artifacts.map(a=><li key={a.id}><button type="button" disabled={archived} onClick={()=>onArtifact(a.id)}>Add artifact {a.id}</button> · {a.size} bytes · {a.sha256}</li>)}</ul>
  </section>
}
