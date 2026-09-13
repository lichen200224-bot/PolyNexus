"""Current-user Windows DPAPI SecretRef provider in an explicit private root.

No enumeration of OS credentials, ambient credential import, or fallback store.
Only metadata references may leave this dedicated boundary. The caller must
keep resolved values out of ordinary Domain/artifact/log/export objects.
"""
from __future__ import annotations
import ctypes
import os
import re
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4
from polynexus_core.storage.content import _plain as _content_plain, ContentError

def _plain(path):
    try:_content_plain(path)
    except ContentError:raise SecretStoreError("secret_path_unsupported") from None


class SecretStoreError(ValueError):
    pass


@dataclass(frozen=True)
class SecretRef:
    reference: str

    def __post_init__(self):
        if not re.fullmatch(r"secretref:[0-9a-f]{32}",self.reference):
            raise SecretStoreError("secret_reference_invalid")


class _Blob(ctypes.Structure):
    _fields_=[('size',ctypes.c_uint32),('data',ctypes.POINTER(ctypes.c_ubyte))]


def _dpapi(content: bytes, *, decrypt: bool) -> bytes:
    if os.name!='nt':
        raise SecretStoreError("os_secret_provider_unavailable")
    buffer=ctypes.create_string_buffer(content)
    incoming=_Blob(len(content),ctypes.cast(buffer,ctypes.POINTER(ctypes.c_ubyte)))
    outgoing=_Blob()
    crypt=ctypes.WinDLL('crypt32',use_last_error=True)
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.LocalFree.argtypes=[ctypes.c_void_p];kernel.LocalFree.restype=ctypes.c_void_p
    function=crypt.CryptUnprotectData if decrypt else crypt.CryptProtectData
    function.argtypes=[ctypes.POINTER(_Blob),ctypes.c_void_p,ctypes.POINTER(_Blob),ctypes.c_void_p,ctypes.c_void_p,ctypes.c_uint32,ctypes.POINTER(_Blob)]
    function.restype=ctypes.c_int
    try:
        if not function(ctypes.byref(incoming),None,None,None,None,1,ctypes.byref(outgoing)):
            raise SecretStoreError("os_secret_operation_failed")
        return ctypes.string_at(outgoing.data,outgoing.size)
    finally:
        ctypes.memset(buffer,0,len(content))
        if outgoing.data:
            ctypes.memset(outgoing.data,0,outgoing.size)
            kernel.LocalFree(ctypes.cast(outgoing.data,ctypes.c_void_p))


class OsSecretStore:
    def __init__(self,root: Path):
        if os.name!='nt' or not root.is_absolute():
            raise SecretStoreError("os_secret_provider_unavailable")
        for ancestor in [root,*root.parents]:
            if ancestor.exists():
                _plain(ancestor)
        root.mkdir(parents=True,exist_ok=True)
        self.root=root.resolve(strict=True)

    def _path(self,ref):
        if not isinstance(ref,SecretRef):
            raise SecretStoreError("secret_reference_invalid")
        _plain(self.root)
        return self.root/ref.reference.split(':')[1]

    def put(self,secret: bytes) -> SecretRef:
        if not isinstance(secret,bytes) or not secret or len(secret)>16384:
            raise SecretStoreError("secret_value_invalid")
        encrypted=_dpapi(secret,decrypt=False)
        ref=SecretRef('secretref:'+uuid4().hex)
        try:
            with self._path(ref).open('xb') as output:
                output.write(encrypted);output.flush();os.fsync(output.fileno())
        except OSError:
            raise SecretStoreError("secret_store_write_failed") from None
        return ref

    def resolve(self,ref: SecretRef) -> bytes:
        try:
            path=self._path(ref);_plain(path)
            before=path.stat()
            with path.open('rb') as source:
                opened=os.fstat(source.fileno())
                encrypted=source.read(32769)
                after=os.fstat(source.fileno())
            _plain(path);current=path.stat()
            identity=lambda value:(value.st_dev,value.st_ino,value.st_size,value.st_mtime_ns)
            if len({identity(value) for value in (before,opened,after,current)})!=1:
                raise SecretStoreError('secret_identity_changed')
            if len(encrypted)>32768:
                raise SecretStoreError("secret_store_invalid")
            return _dpapi(encrypted,decrypt=True)
        except OSError:
            raise SecretStoreError("secret_reference_unavailable") from None

    def remove(self,ref: SecretRef):
        try:
            path=self._path(ref);_plain(path);path.unlink()
        except OSError:
            raise SecretStoreError("secret_reference_unavailable") from None


    def validate(self,ref):
        try:
            path=self._path(ref);_plain(path)
            if not path.is_file():raise SecretStoreError('secret_reference_unavailable')
        except OSError:raise SecretStoreError('secret_reference_unavailable') from None


from contextvars import ContextVar
from contextlib import contextmanager
_active_secret=ContextVar('polynexus_dedicated_secret',default=None)

def active_secret():
    value=_active_secret.get()
    if value is None:raise SecretStoreError('secret_resolution_outside_dispatch')
    return bytes(value)

def redact_active_secret(text):
    value=_active_secret.get()
    if value is None:return text
    import base64
    from urllib.parse import quote
    raw=bytes(value);decoded=raw.decode('utf-8',errors='replace')
    variants={decoded,base64.b64encode(raw).decode(),raw.hex(),quote(decoded,safe='')}
    for secret in sorted(variants,key=len,reverse=True):
        if secret:text=text.replace(secret,'[REDACTED]')
    # Protect meaningful literal fragments without retaining a global secret registry.
    if len(decoded)>=8:
        for index in range(len(decoded)-7):text=text.replace(decoded[index:index+8],'[REDACTED]')
    return text

@contextmanager
def secret_dispatch_scope(reference):
    if reference is None:
        yield
        return
    root=os.environ.get('POLYNEXUS_SECRET_ROOT')
    if not root:raise SecretStoreError('secret_store_not_configured')
    value=bytearray(OsSecretStore(Path(root)).resolve(SecretRef(reference)))
    token=_active_secret.set(value)
    try:yield
    finally:
        _active_secret.reset(token)
        for index in range(len(value)):value[index]=0
