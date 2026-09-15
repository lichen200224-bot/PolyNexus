"""Exact in-process owned handles; restart loses proof and fails closed.

This registry does not discover or kill processes by PID/name/port. D1a can
register only a controlled leaf process. Child-tree ownership belongs to the
launcher boundary and must not be inferred from this leaf proof.
"""
from __future__ import annotations
from dataclasses import dataclass
from subprocess import Popen
from polynexus_core.domain.generation import WorkGenerationRef, GenerationConflict


@dataclass(frozen=True)
class _OwnedLeaf:
    ref: WorkGenerationRef
    run_id: str
    fence: int
    process: Popen


class OwnedProcessRegistry:
    def __init__(self):
        self._owned = {}
        self._adapter_cleanup = {}
        self._jobs = {}

    def register_controlled_leaf(self, ref, run_id, fence, process):
        if not isinstance(process, Popen) or fence < 1 or not run_id:
            raise GenerationConflict("owned_handle_invalid")
        key=(ref.task_id,ref.generation_revision,run_id,fence)
        if key in self._owned:
            if self._owned[key].process is not process:
                raise GenerationConflict("owned_handle_conflict")
            return
        self._owned[key]=_OwnedLeaf(ref,run_id,fence,process)

    def register_controlled_job(self, ref, run_id, fence, job):
        if not isinstance(job, ControlledJob) or not run_id or fence<1:
            raise GenerationConflict('owned_handle_invalid')
        key=(ref.task_id,ref.generation_revision,run_id,fence)
        if key in self._jobs and self._jobs[key] is not job:raise GenerationConflict('owned_handle_conflict')
        self._jobs[key]=job

    def stopped(self, ref, run_id, fence):
        job=self._jobs.get((ref.task_id,ref.generation_revision,run_id,fence))
        if job is not None:return job.stopped()

        entry=self._owned.get((ref.task_id,ref.generation_revision,run_id,fence))
        return (entry is not None and entry.process.poll() is not None) or self._adapter_cleanup.get((ref.task_id,ref.generation_revision,run_id,fence)) is True

    async def cleanup_adapter(self,ref,run_id,fence,adapter,runtime_ref):
        import asyncio
        key=(ref.task_id,ref.generation_revision,run_id,fence)
        self._adapter_cleanup[key]=False
        if runtime_ref is None:return False
        if isinstance(adapter,CleanupObservation) and adapter.attempted:
            self._adapter_cleanup[key]=adapter.verified
            return adapter.verified
        try:
            result=await asyncio.wait_for(adapter.cleanup(runtime_ref),timeout=10)
            self._adapter_cleanup[key]=result is True
        except Exception:
            pass
        return self._adapter_cleanup[key]

    def cancel(self, ref, run_id, fence, timeout=10):
        job=self._jobs.get((ref.task_id,ref.generation_revision,run_id,fence))
        if job is not None:return job.stop(timeout=min(timeout,60))

        entry=self._owned.get((ref.task_id,ref.generation_revision,run_id,fence))
        if entry is None:
            raise GenerationConflict("owned_handle_unknown")
        if entry.process.poll() is None:
            entry.process.terminate()
            entry.process.wait(timeout=min(timeout,60))
        return entry.process.returncode


class ActiveOperations:
    """Exact task handles scoped to generation; no PID discovery or takeover."""
    def __init__(self):self.entries={}
    def register(self,ref,run_id,task):
        key=(ref.task_id,ref.generation_revision,run_id)
        if key in self.entries and self.entries[key] is not task:raise GenerationConflict('active_operation_conflict')
        self.entries[key]=task
    def unregister(self,ref,run_id,task):
        key=(ref.task_id,ref.generation_revision,run_id)
        if self.entries.get(key) is task:self.entries.pop(key)
    def request_cancel_generation(self,ref):
        for (task_id,revision,run_id),operation in list(self.entries.items()):
            if (task_id,revision)==(ref.task_id,ref.generation_revision) and not operation.done():operation.cancel()
    def request_cancel_run(self,ref,run_id):
        operation=self.entries.get((ref.task_id,ref.generation_revision,run_id))
        if operation is not None and not operation.done():operation.cancel();return True
        return False

active_operations=ActiveOperations()


class CleanupObservation:
    """Observe the existing adapter cleanup call without issuing a second one.

    This private per-operation view preserves the public adapter method set.
    Only the actual returned cleanup result is evidence; exceptions/cancel are
    incomplete proof. Registry resolution still validates the wrapped adapter.
    """
    def __init__(self,adapter):
        self.adapter=adapter;self.attempted=False;self.verified=False
    def __getattr__(self,name):return getattr(self.adapter,name)
    async def cleanup(self,runtime_ref):
        self.attempted=True;self.verified=False
        value=await self.adapter.cleanup(runtime_ref)
        self.verified=value is True
        return value


class ControlledJob:
    """Private Windows controlled-runner Job; assignment precedes root execution.

    Only exact retained handles can establish stop. No ambient process scan or
    PID-only takeover is supported. The caller supplies a bounded local runner.
    """
    def __init__(self, argv, cwd, *, environment=None, interactive=False):
        import hashlib, os,ctypes,subprocess,threading,queue
        from pathlib import Path
        if os.name!='nt' or not Path(cwd).is_absolute():raise GenerationConflict('owned_job_unavailable')
        self.c=ctypes;self.handles=[];self.handle=None;self.root=None
        self._closed=False;self._cached_facts=[]
        self.argv=tuple(str(value) for value in argv);self.cwd=str(Path(cwd))
        self._environment=dict(environment or self._safe_environment(os.environ))
        self._stdout_read=None;self._stderr_read=None;self._stdout=b'';self._stderr=b''
        self._termination_signal='none'
        self._stdout_thread=None;self._stderr_thread=None;self._output_error=False
        self._interactive=bool(interactive)
        self._stdin_fd=None;self._stdin_lock=threading.Lock()
        self._stdout_lines=queue.Queue() if interactive else None
        self._output_truncated=False
        self._hashlib=hashlib;self._os=os
        c=ctypes;U=c.c_uint32;P=c.c_void_p;Z=c.c_size_t;Q=c.c_uint64
        class Basic(c.Structure):
            _fields_=[('process_time',c.c_int64),('job_time',c.c_int64),('flags',U),('min_ws',Z),('max_ws',Z),('active_limit',U),('affinity',Z),('priority',U),('scheduling',U)]
        class Extended(c.Structure):
            _fields_=[('basic',Basic),('io',Q*6),('process_memory',Z),('job_memory',Z),('peak_process',Z),('peak_job',Z)]
        class Startup(c.Structure):
            _fields_=[('cb',U),('reserved',P),('desktop',P),('title',P),('x',U),('y',U),('width',U),('height',U),('chars_x',U),('chars_y',U),('fill',U),('flags',U),('show',c.c_uint16),('reserved2_size',c.c_uint16),('reserved2',P),('stdin',P),('stdout',P),('stderr',P)]
        class Process(c.Structure):
            _fields_=[('process',P),('thread',P),('pid',U),('tid',U)]
        class Accounting(c.Structure):
            _fields_=[('user',c.c_int64),('kernel',c.c_int64),('period_user',c.c_int64),('period_kernel',c.c_int64),('faults',U),('total',U),('active',U),('terminated',U)]
        self.Accounting=Accounting
        k=c.WinDLL('kernel32',use_last_error=True);self.k=k
        declarations={
          'CreateJobObjectW':([P,c.c_wchar_p],P),
          'SetInformationJobObject':([P,c.c_int,P,U],c.c_int),
          'CreateProcessW':([c.c_wchar_p,c.c_wchar_p,P,P,c.c_int,U,P,c.c_wchar_p,P,P],c.c_int),
          'CreatePipe':([P,P,P,U],c.c_int),'SetHandleInformation':([P,U,U],c.c_int),
          'AssignProcessToJobObject':([P,P],c.c_int),'ResumeThread':([P],U),
          'TerminateProcess':([P,U],c.c_int),'TerminateJobObject':([P,U],c.c_int),
          'WaitForSingleObject':([P,U],U),'CloseHandle':([P],c.c_int),
          'GetExitCodeProcess':([P,P],c.c_int),'GetProcessTimes':([P,P,P,P,P],c.c_int),
          'QueryInformationJobObject':([P,c.c_int,P,U,P],c.c_int),
          'OpenProcess':([U,c.c_int,U],P),'IsProcessInJob':([P,P,P],c.c_int)}
        for name,(args,result) in declarations.items():
            function=getattr(k,name);function.argtypes=args;function.restype=result
        self.handle=k.CreateJobObjectW(None,None)
        if not self.handle:raise GenerationConflict('owned_job_create_failed')
        limits=Extended();limits.basic.flags=0x2000
        if not k.SetInformationJobObject(self.handle,9,c.byref(limits),c.sizeof(limits)):
            k.CloseHandle(self.handle);self.handle=None;raise GenerationConflict('owned_job_limits_failed')
        class SecurityAttributes(c.Structure):
            _fields_=[('length',U),('descriptor',P),('inherit',c.c_int)]
        security=SecurityAttributes(c.sizeof(SecurityAttributes),None,1)
        stdout_read=P();stdout_write=P();stderr_read=P();stderr_write=P()
        if not k.CreatePipe(c.byref(stdout_read),c.byref(stdout_write),c.byref(security),0):
            k.CloseHandle(self.handle);self.handle=None;raise GenerationConflict('owned_stdout_pipe_failed')
        if not k.CreatePipe(c.byref(stderr_read),c.byref(stderr_write),c.byref(security),0):
            k.CloseHandle(stdout_read);k.CloseHandle(stdout_write);k.CloseHandle(self.handle);self.handle=None
            raise GenerationConflict('owned_stderr_pipe_failed')
        if not k.SetHandleInformation(stdout_read,1,0) or not k.SetHandleInformation(stderr_read,1,0):
            k.CloseHandle(stdout_read);k.CloseHandle(stdout_write);k.CloseHandle(stderr_read);k.CloseHandle(stderr_write);k.CloseHandle(self.handle);self.handle=None
            raise GenerationConflict('owned_pipe_inherit_failed')
        stdin_read=P();stdin_write=P()
        if self._interactive:
            if not k.CreatePipe(c.byref(stdin_read),c.byref(stdin_write),c.byref(security),0) or not k.SetHandleInformation(stdin_write,1,0):
                k.CloseHandle(stdout_read);k.CloseHandle(stdout_write);k.CloseHandle(stderr_read);k.CloseHandle(stderr_write);k.CloseHandle(self.handle);self.handle=None
                raise GenerationConflict('owned_stdin_pipe_failed')
        self._stdout_read=int(stdout_read.value or 0);self._stderr_read=int(stderr_read.value or 0)
        startup=Startup();startup.cb=c.sizeof(startup);startup.flags=0x100;startup.stdout=stdout_write;startup.stderr=stderr_write
        if self._interactive:startup.stdin=stdin_read
        process=Process()
        environment_block=''.join(f'{key}={value}\0' for key,value in sorted(self._environment.items(),key=lambda item:item[0].upper()))+'\0'
        environment_buffer=c.create_unicode_buffer(environment_block)
        try:
            command=c.create_unicode_buffer(subprocess.list2cmdline([str(x) for x in argv]))
            if not k.CreateProcessW(str(argv[0]),command,None,None,True,0x08000404,c.cast(environment_buffer,P),str(cwd),c.byref(startup),c.byref(process)):
                raise GenerationConflict('owned_process_create_failed')
            try:
                if not k.AssignProcessToJobObject(self.handle,process.process):raise GenerationConflict('owned_job_assignment_failed')
                if self._interactive:
                    k.CloseHandle(stdin_read);stdin_read.value=None
                    import msvcrt
                    self._stdin_fd=msvcrt.open_osfhandle(int(stdin_write.value),os.O_WRONLY|os.O_BINARY)
                    stdin_write.value=None
                if k.ResumeThread(process.thread)==0xffffffff:raise GenerationConflict('owned_process_resume_failed')
                self.root=(process.pid,process.process);self.handles.append(self.root)
                self._stdout_thread=threading.Thread(target=self._drain_pipe,args=('_stdout_read','_stdout'),daemon=True)
                self._stderr_thread=threading.Thread(target=self._drain_pipe,args=('_stderr_read','_stderr'),daemon=True)
                self._stdout_thread.start();self._stderr_thread.start()
            except BaseException:
                self.close_stdin()
                k.TerminateProcess(process.process,1);k.WaitForSingleObject(process.process,5000);k.CloseHandle(process.process);raise
            finally:
                k.CloseHandle(process.thread)
                if stdout_write.value:
                    k.CloseHandle(stdout_write);stdout_write.value=None
                if stderr_write.value:
                    k.CloseHandle(stderr_write);stderr_write.value=None
        except BaseException:
            if stdout_write.value:k.CloseHandle(stdout_write)
            if stderr_write.value:k.CloseHandle(stderr_write)
            if stdin_read.value:k.CloseHandle(stdin_read)
            if stdin_write.value:k.CloseHandle(stdin_write)
            if self._stdout_read:k.CloseHandle(self._stdout_read);self._stdout_read=None
            if self._stderr_read:k.CloseHandle(self._stderr_read);self._stderr_read=None
            k.CloseHandle(self.handle);self.handle=None;raise

    @staticmethod
    def _safe_environment(source):
        names={'COMSPEC','PATHEXT','PATH','SYSTEMDRIVE','SYSTEMROOT','TEMP','TMP','WINDIR'}
        return {name:value for name,value in source.items() if name in names}

    def retain_descendant(self,pid):
        # PID is only a lookup hint from the owned runner. Exact job membership
        # and retained creation-time identity are mandatory before acceptance.
        c=self.c;handle=self.k.OpenProcess(0x1000|0x100000,False,pid)
        if not handle:raise GenerationConflict('owned_child_open_failed')
        member=c.c_int()
        if not self.k.IsProcessInJob(handle,self.handle,c.byref(member)) or not member.value:
            self.k.CloseHandle(handle);raise GenerationConflict('owned_child_not_in_job')
        entry=(pid,handle)
        if self._facts(entry)['created_filetime']<self._facts(self.root)['created_filetime']:
            self.k.CloseHandle(handle);raise GenerationConflict('owned_child_identity_invalid')
        self.handles.append(entry)
        return self._facts(entry)

    def _facts(self,entry):
        c=self.c;created=c.c_uint64();ended=c.c_uint64();kernel=c.c_uint64();user=c.c_uint64();code=c.c_uint32()
        if not self.k.GetProcessTimes(entry[1],c.byref(created),c.byref(ended),c.byref(kernel),c.byref(user)) or not self.k.GetExitCodeProcess(entry[1],c.byref(code)):
            raise GenerationConflict('owned_process_observation_failed')
        return {'pid':entry[0],'retained_handle':int(entry[1]),'created_filetime':created.value,'ended_filetime':ended.value,'exit_code':code.value,'stopped':self.k.WaitForSingleObject(entry[1],0)==0,'argv':self.argv,'cwd':self.cwd,'signal':self._termination_signal}

    def facts(self):
        if self._closed:
            return list(self._cached_facts)
        self._cached_facts=[self._facts(entry) for entry in self.handles]
        if self._cached_facts and all(bool(item['stopped']) for item in self._cached_facts):
            stdout,stderr=self.output()
            for item in self._cached_facts:
                item['stdout_bytes']=len(stdout);item['stderr_bytes']=len(stderr)
                item['stdout_sha256']=self._hashlib.sha256(stdout).hexdigest();item['stderr_sha256']=self._hashlib.sha256(stderr).hexdigest()
        return list(self._cached_facts)

    def stopped(self):
        if self._closed:return bool(self._cached_facts) and all(item['stopped'] for item in self._cached_facts)
        c=self.c;accounting=self.Accounting()
        if not self.handle or not self.k.QueryInformationJobObject(self.handle,1,c.byref(accounting),c.sizeof(accounting),None):return False
        return accounting.active==0 and all(self.k.WaitForSingleObject(handle,0)==0 for _,handle in self.handles)

    def stop(self,timeout=10):
        import time
        if not self.stopped():
            self._termination_signal='job_terminate'
            if not self.k.TerminateJobObject(self.handle,1):raise GenerationConflict('owned_job_stop_failed')
        deadline=time.monotonic()+min(timeout,60)
        while not self.stopped():
            if time.monotonic()>=deadline:raise GenerationConflict('owned_job_stop_unverified')
            time.sleep(.01)
        return self._facts(self.root)['exit_code']

    def dispose(self):
        if self._closed:return
        self.close_stdin()
        if self.handle:
            self.stop()
            self._cached_facts=self.facts()
            for _,handle in self.handles:self.k.CloseHandle(handle)
            self.k.CloseHandle(self.handle);self.handle=None
        self._closed=True

    def output(self):
        if self._stdout_thread is None and self._stderr_thread is None:
            return self._stdout,self._stderr
        for thread in (self._stdout_thread,self._stderr_thread):
            if thread is not None:thread.join(timeout=10)
        if any(thread is not None and thread.is_alive() for thread in (self._stdout_thread,self._stderr_thread)) or self._output_error:
            raise GenerationConflict('owned_output_observation_failed')
        return self._stdout,self._stderr

    def send_line(self,data):
        """Send one bounded newline-delimited request to this owned child."""
        if not self._interactive or self._stdin_fd is None or not isinstance(data,bytes) or len(data)>1024*1024 or not data.endswith(b'\n'):
            raise GenerationConflict('owned_stdin_invalid')
        with self._stdin_lock:
            offset=0
            while offset<len(data):
                written=self._os.write(self._stdin_fd,data[offset:])
                if written<=0:raise GenerationConflict('owned_stdin_write_failed')
                offset+=written

    def read_line(self,timeout):
        """Receive a complete stdout line while the retained Job is live."""
        if not self._interactive:
            raise GenerationConflict('owned_stdout_not_interactive')
        try:
            line=self._stdout_lines.get(timeout=timeout)
        except Exception as exc:
            raise TimeoutError('owned_stdout_timeout') from exc
        if line is None:raise GenerationConflict('owned_stdout_closed')
        return line

    def close_stdin(self):
        if not self._interactive:return
        with self._stdin_lock:
            if self._stdin_fd is not None:
                self._os.close(self._stdin_fd)
                self._stdin_fd=None

    def _drain_pipe(self,handle_field,value_field):
        handle=getattr(self,handle_field)
        setattr(self,handle_field,None)
        if not handle:return
        try:
            import msvcrt
            fd=msvcrt.open_osfhandle(handle,self._os.O_RDONLY|self._os.O_BINARY)
            data=[];remaining=4*1024*1024;pending=b''
            while True:
                chunk=self._os.read(fd,65536)
                if not chunk:break
                if remaining>0:
                    kept=chunk[:remaining];data.append(kept);remaining-=len(kept)
                    if self._interactive and value_field=='_stdout':
                        pending+=kept
                        while b'\n' in pending:
                            line,pending=pending.split(b'\n',1)
                            self._stdout_lines.put(line+b'\n')
                elif self._interactive and value_field=='_stdout':
                    self._output_truncated=True
            self._os.close(fd)
            setattr(self,value_field,b''.join(data))
            if self._interactive and value_field=='_stdout' and pending:
                self._stdout_lines.put(pending)
        except (OSError,ValueError):
            self._output_error=True
        finally:
            if self._interactive and value_field=='_stdout':
                self._stdout_lines.put(None)
