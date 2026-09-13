"""Bounded managed Git inputs; never change the source index/working files."""
from __future__ import annotations
import hashlib,json,os,stat,subprocess
from pathlib import Path
from polynexus_core.storage.content import ContentStore,ContentError,_plain,MAX_CONTENT_BYTES


def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode("utf-8")


def snapshot(entries):
    paths=[e['path'] for e in entries]
    if len(paths)!=len(set(p.casefold() for p in paths)):
        raise ContentError('snapshot_path_collision')
    return {'entries':sorted(entries,key=lambda e:e['path'].encode('utf-8')),'format':'pn.snapshot.v1'}


def relative_path(value):
    if not isinstance(value,str) or not value or '\\' in value or ':' in value or value.startswith('/') or any(x in ('','.', '..') for x in value.split('/')):
        raise ContentError('input_path_invalid')
    if any(part.casefold()=='.git' or part.endswith((' ','.')) or part.split('.')[0].upper() in {'CON','PRN','AUX','NUL',*[f'COM{i}' for i in range(1,10)],*[f'LPT{i}' for i in range(1,10)]} or any(ord(c)<32 for c in part) for part in value.split('/')):
        raise ContentError('input_path_invalid')
    return value


def safe_source(root,value):
    path=root/relative_path(value)
    for p in [path,*path.parents]:
        if p==root.parent:break
        if p.exists() or p.is_symlink():_plain(p)
    if not path.resolve(strict=False).is_relative_to(root):raise ContentError('input_path_escape')
    return path


def read_selected(root,value):
    path=safe_source(root,value)
    before=path.stat()
    if not stat.S_ISREG(before.st_mode):raise ContentError('input_not_regular')
    with path.open('rb') as stream:
        opened=os.fstat(stream.fileno());data=stream.read(MAX_CONTENT_BYTES+1);after=os.fstat(stream.fileno())
    current=safe_source(root,value).stat()
    keys=lambda s:(s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns)
    if keys(before)!=keys(opened) or keys(opened)!=keys(after) or keys(after)!=keys(current):raise ContentError('input_changed_during_read')
    if len(data)>MAX_CONTENT_BYTES:raise ContentError('input_too_large')
    return data


class ManagedInputs:
    def __init__(self,store: ContentStore,source_root: Path,work_root: Path):
        self.store=store
        for root in (source_root,work_root):
            if not root.is_absolute():raise ContentError('workspace_root_invalid')
            for p in [root,*root.parents]:
                if p.exists():_plain(p)
        self.source_root=source_root.resolve();self.work_root=work_root.resolve()
        self.work_root.mkdir(parents=True,exist_ok=True)
        self.hooks=self.work_root/'empty-hooks';self.hooks.mkdir(exist_ok=True)

    def repository(self,relative):
        repo=safe_source(self.source_root,relative)
        if not repo.is_dir():raise ContentError('repository_unavailable')
        return repo

    def git(self,repo,*args):
        result=subprocess.run(['git','--no-optional-locks','-c','core.fsmonitor=false','-c','core.hooksPath='+str(self.hooks),'-c','safe.directory='+repo.as_posix(),'-C',str(repo),*args],capture_output=True,timeout=30)
        if result.returncode:raise ContentError('git_operation_failed')
        return result.stdout

    def inspect(self,relative):
        repo=self.repository(relative)
        status=self.git(repo,'status','--porcelain=v1','-z','--untracked-files=all')
        paths=[]
        for record in status.split(b'\0'):
            if not record:continue
            flag=record[:2].decode('ascii');path=record[3:].decode('utf-8')
            if 'R' in flag or 'C' in flag or 'U' in flag:raise ContentError('unsupported_git_state')
            paths.append(relative_path(path))
        return {'repository':relative,'baseline_commit':self.git(repo,'rev-parse','HEAD').decode().strip(),'dirty_paths':paths}

    def capture(self,relative,baseline,selected):
        repo=self.repository(relative)
        index_path=Path(self.git(repo,'rev-parse','--path-format=absolute','--git-path','index').decode().strip())
        index_before=index_path.read_bytes() if index_path.exists() else b''
        fact=self.inspect(relative)
        if baseline!=fact['baseline_commit']:raise ContentError('baseline_changed')
        if len(selected)!=len(set(selected)) or not set(selected)<=set(fact['dirty_paths']):raise ContentError('dirty_selection_invalid')
        # Inert global filter registrations are not execution. Active filter
        # attributes on captured paths are unsupported and rejected below.

        before_status=self.git(repo,'status','--porcelain=v1','-z','--untracked-files=all')
        entries={};total=0
        for record in self.git(repo,'ls-tree','-rz','--full-tree',baseline).split(b'\0'):
            if not record:continue
            info,raw=record.split(b'\t',1);mode,kind,oid=info.decode().split();path=relative_path(raw.decode('utf-8'))
            if kind!='blob' or mode not in ('100644','100755'):raise ContentError('unsupported_git_entry')
            data=self.git(repo,'cat-file','blob',oid);total+=len(data)
            if path.split('/')[-1]=='.gitattributes' and b'filter' in data:raise ContentError('unsupported_git_filter')
            if total>MAX_CONTENT_BYTES:raise ContentError('snapshot_too_large')
            digest,size=self.store.put(data);entries[path]={'path':path,'kind':'file','mode':mode,'blob':'sha256:'+digest,'size':size}
        base=snapshot(list(entries.values()))
        for path in selected:
            target=safe_source(repo,path)
            if not target.exists():entries.pop(path,None);continue
            data=read_selected(repo,path);digest,size=self.store.put(data)
            entries[path]={'path':path,'kind':'file','mode':entries.get(path,{}).get('mode','100644'),'blob':'sha256:'+digest,'size':size}
        attribute_paths=sorted(set(entries)|set(selected))
        if attribute_paths:
            check=subprocess.run(['git','--no-optional-locks','-c','core.fsmonitor=false','-c','safe.directory='+repo.as_posix(),'-C',str(repo),'check-attr','-z','filter','--stdin'],input=b'\0'.join(p.encode('utf-8') for p in attribute_paths)+b'\0',capture_output=True,timeout=30)
            values=check.stdout.split(b'\0')
            if check.returncode or any(value not in (b'unspecified',b'unset') for value in values[2::3]):raise ContentError('unsupported_git_filter')
        result=snapshot(list(entries.values()))
        if self.git(repo,'rev-parse','HEAD').decode().strip()!=baseline or (index_path.read_bytes() if index_path.exists() else b'')!=index_before or self.git(repo,'status','--porcelain=v1','-z','--untracked-files=all')!=before_status:
            raise ContentError('source_changed_during_capture')
        return {'repository':relative,'scope_id':hashlib.sha256(os.path.normcase(str(repo.resolve())).encode()).hexdigest(),'baseline_commit':baseline,'baseline':base,'selected':list(selected),'input':result,'source_index_sha256':hashlib.sha256(index_before).hexdigest()}

    def materialize(self,record,workspace_id):
        # Core-generated workspace id only; caller cannot supply a destination.
        if not workspace_id.startswith('workspace_') or not workspace_id[10:].isalnum():raise ContentError('workspace_identity_invalid')
        destination=self.work_root/workspace_id
        if destination.exists():raise ContentError('workspace_already_exists')
        repo=self.repository(record['repository'])
        self.git(repo,'worktree','add','--detach','--no-checkout',str(destination),record['baseline_commit'])
        try:
            self.git(destination,'read-tree',record['baseline_commit'])
            for entry in record['input']['entries']:
                path=safe_source(destination,entry['path']);path.parent.mkdir(parents=True,exist_ok=True)
                data=self.store.read(entry['blob'][7:],entry['size'])
                with path.open('xb') as stream:stream.write(data)
                if os.name!='nt':path.chmod(0o755 if entry['mode']=='100755' else 0o644)
            return destination
        except Exception:
            # Preserve partial managed workspace for recovery; never clean source.
            raise ContentError('workspace_setup_incomplete') from None
