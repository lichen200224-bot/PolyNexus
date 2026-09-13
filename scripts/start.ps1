$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$hostExecutable = (Get-Process -Id $PID).Path
$tokenBytes = New-Object byte[] 32
$random = [System.Security.Cryptography.RandomNumberGenerator]::Create()
try {
  $random.GetBytes($tokenBytes)
} finally {
  $random.Dispose()
}
$token = [Convert]::ToBase64String($tokenBytes).TrimEnd('=').Replace('+', '-').Replace('/', '_')

$previousLoopbackToken = [Environment]::GetEnvironmentVariable("LOOPBACK_TOKEN", "Process")
$previousViteToken = [Environment]::GetEnvironmentVariable(
  "VITE_POLYNEXUS_LOOPBACK_TOKEN",
  "Process"
)
$coreProcess = $null
$webProcess = $null

if (-not ("PolyNexus.NativeJob" -as [type])) {
  Add-Type -TypeDefinition @"
using System;
using System.ComponentModel;
using System.Diagnostics;
using System.Runtime.InteropServices;
using System.Text;

namespace PolyNexus {
  public sealed class NativeJob : IDisposable {
    private IntPtr handle;

    [StructLayout(LayoutKind.Sequential)]
    private struct BasicLimitInformation {
      public long PerProcessUserTimeLimit;
      public long PerJobUserTimeLimit;
      public uint LimitFlags;
      public UIntPtr MinimumWorkingSetSize;
      public UIntPtr MaximumWorkingSetSize;
      public uint ActiveProcessLimit;
      public UIntPtr Affinity;
      public uint PriorityClass;
      public uint SchedulingClass;
    }

    [StructLayout(LayoutKind.Sequential)]
    private struct IoCounters {
      public ulong ReadOperationCount;
      public ulong WriteOperationCount;
      public ulong OtherOperationCount;
      public ulong ReadTransferCount;
      public ulong WriteTransferCount;
      public ulong OtherTransferCount;
    }

    [StructLayout(LayoutKind.Sequential)]
    private struct ExtendedLimitInformation {
      public BasicLimitInformation BasicLimitInformation;
      public IoCounters IoInfo;
      public UIntPtr ProcessMemoryLimit;
      public UIntPtr JobMemoryLimit;
      public UIntPtr PeakProcessMemoryUsed;
      public UIntPtr PeakJobMemoryUsed;
    }

    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
    private struct StartupInformation {
      public uint cb;
      public string lpReserved;
      public string lpDesktop;
      public string lpTitle;
      public uint dwX;
      public uint dwY;
      public uint dwXSize;
      public uint dwYSize;
      public uint dwXCountChars;
      public uint dwYCountChars;
      public uint dwFillAttribute;
      public uint dwFlags;
      public short wShowWindow;
      public short cbReserved2;
      public IntPtr lpReserved2;
      public IntPtr hStdInput;
      public IntPtr hStdOutput;
      public IntPtr hStdError;
    }

    [StructLayout(LayoutKind.Sequential)]
    private struct ProcessInformation {
      public IntPtr hProcess;
      public IntPtr hThread;
      public uint dwProcessId;
      public uint dwThreadId;
    }

    [DllImport("kernel32.dll", CharSet = CharSet.Unicode)]
    private static extern IntPtr CreateJobObject(IntPtr attributes, string name);

    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern bool SetInformationJobObject(
      IntPtr job,
      int informationClass,
      ref ExtendedLimitInformation information,
      uint informationLength
    );

    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern bool AssignProcessToJobObject(IntPtr job, IntPtr process);

    [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
    private static extern bool CreateProcess(
      string applicationName,
      StringBuilder commandLine,
      IntPtr processAttributes,
      IntPtr threadAttributes,
      bool inheritHandles,
      uint creationFlags,
      IntPtr environment,
      string currentDirectory,
      ref StartupInformation startupInformation,
      out ProcessInformation processInformation
    );

    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern uint ResumeThread(IntPtr thread);

    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern bool TerminateProcess(IntPtr process, uint exitCode);

    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern uint WaitForSingleObject(IntPtr handle, uint milliseconds);

    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern bool CloseHandle(IntPtr handle);

    private const uint CreateSuspended = 0x00000004;
    private const uint CreateNoWindow = 0x08000000;
    private const uint ResumeFailed = 0xffffffff;

    private static string QuoteArgument(string value) {
      return "\"" + value.Replace("\"", "\\\"") + "\"";
    }

    public NativeJob() {
      handle = CreateJobObject(IntPtr.Zero, null);
      if (handle == IntPtr.Zero) throw new Win32Exception();
      var information = new ExtendedLimitInformation();
      information.BasicLimitInformation.LimitFlags = 0x00002000;
      if (!SetInformationJobObject(
        handle,
        9,
        ref information,
        (uint)Marshal.SizeOf(typeof(ExtendedLimitInformation)))) {
        int error = Marshal.GetLastWin32Error();
        CloseHandle(handle);
        handle = IntPtr.Zero;
        throw new Win32Exception(error);
      }
    }

    public Process StartSuspended(
      string executable,
      string[] arguments,
      string workingDirectory
    ) {
      var commandLine = new StringBuilder(QuoteArgument(executable));
      foreach (string argument in arguments) {
        commandLine.Append(" ").Append(QuoteArgument(argument));
      }

      var startup = new StartupInformation();
      startup.cb = (uint)Marshal.SizeOf(typeof(StartupInformation));
      ProcessInformation process;
      if (!CreateProcess(
        executable,
        commandLine,
        IntPtr.Zero,
        IntPtr.Zero,
        false,
        CreateSuspended | CreateNoWindow,
        IntPtr.Zero,
        workingDirectory,
        ref startup,
        out process)) {
        throw new Win32Exception(Marshal.GetLastWin32Error());
      }

      try {
        if (!AssignProcessToJobObject(handle, process.hProcess)) {
          int error = Marshal.GetLastWin32Error();
          TerminateProcess(process.hProcess, 1);
          WaitForSingleObject(process.hProcess, 5000);
          throw new Win32Exception(error);
        }

        if (ResumeThread(process.hThread) == ResumeFailed) {
          int error = Marshal.GetLastWin32Error();
          TerminateProcess(process.hProcess, 1);
          WaitForSingleObject(process.hProcess, 5000);
          throw new Win32Exception(error);
        }

        var managedProcess = Process.GetProcessById((int)process.dwProcessId);
        IntPtr managedHandle = managedProcess.Handle;
        return managedProcess;
      } finally {
        CloseHandle(process.hThread);
        CloseHandle(process.hProcess);
      }
    }

    public void Dispose() {
      if (handle == IntPtr.Zero) return;
      CloseHandle(handle);
      handle = IntPtr.Zero;
    }
  }
}
"@
}

$ownedJob = [PolyNexus.NativeJob]::new()

function Restore-ProcessEnvironment {
  param([string]$Name, $PreviousValue)
  if ($null -eq $PreviousValue) {
    Remove-Item "Env:$Name" -ErrorAction SilentlyContinue
  } else {
    [Environment]::SetEnvironmentVariable($Name, $PreviousValue, "Process")
  }
}

try {
  $env:LOOPBACK_TOKEN = $token
  Remove-Item Env:VITE_POLYNEXUS_LOOPBACK_TOKEN -ErrorAction SilentlyContinue
  $coreScript = Join-Path $PSScriptRoot "start_core.ps1"
  $webScript = Join-Path $PSScriptRoot "start_web.ps1"
  $commonArguments = @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File")

  $coreProcess = $ownedJob.StartSuspended(
    $hostExecutable,
    ($commonArguments + $coreScript),
    $repoRoot
  )

  Remove-Item Env:LOOPBACK_TOKEN -ErrorAction SilentlyContinue
  $env:VITE_POLYNEXUS_LOOPBACK_TOKEN = $token
  $webProcess = $ownedJob.StartSuspended(
    $hostExecutable,
    ($commonArguments + $webScript),
    $repoRoot
  )

  Restore-ProcessEnvironment "LOOPBACK_TOKEN" $previousLoopbackToken
  Restore-ProcessEnvironment "VITE_POLYNEXUS_LOOPBACK_TOKEN" $previousViteToken
  [Array]::Clear($tokenBytes, 0, $tokenBytes.Length)
  $token = $null

  Write-Output "PolyNexus START launched Core at http://127.0.0.1:8765"
  Write-Output "PolyNexus START launched Web at http://127.0.0.1:5173"
  Write-Output "Press Ctrl+C to stop the owned Core and Web process trees."

  while ($true) {
    Start-Sleep -Milliseconds 250
    $coreProcess.Refresh()
    $webProcess.Refresh()
    if ($coreProcess.HasExited -or $webProcess.HasExited) {
      $component = if ($coreProcess.HasExited) { "Core" } else { "Web" }
      $componentProcess = if ($coreProcess.HasExited) { $coreProcess } else { $webProcess }
      throw "PolyNexus START stopped because $component exited with code $($componentProcess.ExitCode)."
    }
  }
} finally {
  Restore-ProcessEnvironment "LOOPBACK_TOKEN" $previousLoopbackToken
  Restore-ProcessEnvironment "VITE_POLYNEXUS_LOOPBACK_TOKEN" $previousViteToken
  $ownedJob.Dispose()
  [Array]::Clear($tokenBytes, 0, $tokenBytes.Length)
  $token = $null
}
