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
    def __init__(self, argv, cwd):
        import os,ctypes,subprocess
        from pathlib import Path
        if os.name!='nt' or not Path(cwd).is_absolute():raise GenerationConflict('owned_job_unavailable')
        self.c=ctypes;self.handles=[];self.handle=None;self.root=None
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
        startup=Startup();startup.cb=c.sizeof(startup);process=Process()
        try:
            command=c.create_unicode_buffer(subprocess.list2cmdline([str(x) for x in argv]))
            if not k.CreateProcessW(str(argv[0]),command,None,None,False,0x08000004,None,str(cwd),c.byref(startup),c.byref(process)):
                raise GenerationConflict('owned_process_create_failed')
            try:
                if not k.AssignProcessToJobObject(self.handle,process.process):raise GenerationConflict('owned_job_assignment_failed')
                if k.ResumeThread(process.thread)==0xffffffff:raise GenerationConflict('owned_process_resume_failed')
                self.root=(process.pid,process.process);self.handles.append(self.root)
            except BaseException:
                k.TerminateProcess(process.process,1);k.WaitForSingleObject(process.process,5000);k.CloseHandle(process.process);raise
            finally:k.CloseHandle(process.thread)
        except BaseException:
            k.CloseHandle(self.handle);self.handle=None;raise

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
        return {'pid':entry[0],'retained_handle':int(entry[1]),'created_filetime':created.value,'ended_filetime':ended.value,'exit_code':code.value,'stopped':self.k.WaitForSingleObject(entry[1],0)==0}

    def facts(self):return [self._facts(entry) for entry in self.handles]

    def stopped(self):
        c=self.c;accounting=self.Accounting()
        if not self.handle or not self.k.QueryInformationJobObject(self.handle,1,c.byref(accounting),c.sizeof(accounting),None):return False
        return accounting.active==0 and all(self.k.WaitForSingleObject(handle,0)==0 for _,handle in self.handles)

    def stop(self,timeout=10):
        import time
        if not self.stopped() and not self.k.TerminateJobObject(self.handle,1):raise GenerationConflict('owned_job_stop_failed')
        deadline=time.monotonic()+min(timeout,60)
        while not self.stopped():
            if time.monotonic()>=deadline:raise GenerationConflict('owned_job_stop_unverified')
            time.sleep(.01)
        return self._facts(self.root)['exit_code']

    def dispose(self):
        if self.handle:
            self.stop()
            for _,handle in self.handles:self.k.CloseHandle(handle)
            self.k.CloseHandle(self.handle);self.handle=None
