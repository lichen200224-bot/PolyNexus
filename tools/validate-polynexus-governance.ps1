[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [string]$RepoRoot = (Get-Location).Path
)

$ErrorActionPreference = 'Stop'

function Add-ValidationError {
    param([string]$Message)
    $script:ValidationErrors += $Message
}

$script:ValidationErrors = @()
$resolvedRoot = (Resolve-Path -LiteralPath $RepoRoot).Path
$governanceRoot = Join-Path $resolvedRoot 'docs\governance\sop-v1.1'
$manifestPath = Join-Path $governanceRoot 'manifest.json'

$requiredFiles = @(
    'docs/governance/sop-v1.1/README.md',
    'docs/governance/sop-v1.1/POLYNEXUS_SOP_v1.1.md',
    'docs/governance/sop-v1.1/STATE_MACHINE.md',
    'docs/governance/sop-v1.1/OUTPUT_CONTRACT.md',
    'docs/governance/sop-v1.1/PROMPT_LIBRARY.md',
    'docs/governance/sop-v1.1/INSTALL_AND_ROLLBACK.md',
    'docs/governance/sop-v1.1/PROTECTED_AREAS.md',
    'docs/governance/sop-v1.1/manifest.md',
    'docs/governance/sop-v1.1/manifest.json',
    'docs/governance/sop-v1.1/templates/AGENT_COMPLETION_TEMPLATE.md',
    'docs/governance/sop-v1.1/templates/TASK_HANDOFF_TEMPLATE.md',
    'docs/governance/sop-v1.1/templates/ACCEPTANCE_REPORT_TEMPLATE.md',
    'docs/governance/sop-v1.1/templates/FIX_PROMPT_TEMPLATE.md',
    'docs/governance/sop-v1.1/templates/REVERIFICATION_PROMPT_TEMPLATE.md',
    'docs/governance/sop-v1.1/templates/ANTIGRAVITY_VERIFICATION_TEMPLATE.md',
    'docs/governance/sop-v1.1/templates/HUMAN_APPROVAL_GATE_TEMPLATE.md',
    'docs/governance/sop-v1.1/schemas/state-machine.json',
    'docs/governance/sop-v1.1/schemas/state-machine.data.json',
    'docs/governance/sop-v1.1/schemas/governance-event.schema.json',
    'tools/validate-polynexus-governance.ps1'
)

foreach ($relativePath in $requiredFiles) {
    $candidate = Join-Path $resolvedRoot ($relativePath -replace '/', '\')
    if (-not (Test-Path -LiteralPath $candidate -PathType Leaf)) {
        Add-ValidationError "Missing required file: $relativePath"
    }
}

if (Test-Path -LiteralPath $manifestPath -PathType Leaf) {
    try {
        $manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json

        if ($manifest.version -ne '1.1.0') {
            Add-ValidationError "Unexpected manifest version: $($manifest.version)"
        }

        if ($manifest.package_mode -ne 'additive') {
            Add-ValidationError "Manifest package_mode must be additive: $($manifest.package_mode)"
        }

        if ($null -ne $manifest.updated_files -and @($manifest.updated_files).Count -ne 0) {
            Add-ValidationError 'Manifest updated_files must be empty for this additive package.'
        }

        $forbiddenPathRegex = '(^|/)(src|app|packages|tests|test|migrations)(/|$)|FVS-01|FVS-02|ADR-00[1-9]|ADR-010'
        $manifestPaths = @()
        foreach ($entry in @($manifest.files)) {
            $relativePath = [string]$entry.path
            $manifestPaths += $relativePath

            if ([System.IO.Path]::IsPathRooted($relativePath) -or $relativePath -match '(^|[\\/])\.\.([\\/]|$)') {
                Add-ValidationError "Unsafe manifest path: $relativePath"
            }

            if ($relativePath -match $forbiddenPathRegex) {
                Add-ValidationError "Manifest path is in a protected or excluded area: $relativePath"
            }

            $candidate = Join-Path $resolvedRoot ($relativePath -replace '/', '\')
            if (-not (Test-Path -LiteralPath $candidate -PathType Leaf)) {
                Add-ValidationError "Manifest file does not exist: $relativePath"
            }

            if ($entry.action -ne 'add') {
                Add-ValidationError "Manifest action must be add: $relativePath -> $($entry.action)"
            }
        }

        $actualGovernanceFiles = @(Get-ChildItem -LiteralPath $governanceRoot -Recurse -File | ForEach-Object {
            $_.FullName.Substring($resolvedRoot.Length + 1).Replace('\', '/')
        })
        $unlistedFiles = @($actualGovernanceFiles | Where-Object { $_ -notin $manifestPaths })
        if ($unlistedFiles.Count -gt 0) {
            Add-ValidationError "Governance files missing from manifest: $($unlistedFiles -join ', ')"
        }

        $stateDataPath = Join-Path $governanceRoot 'schemas\state-machine.data.json'
        $stateSchemaPath = Join-Path $governanceRoot 'schemas\state-machine.json'
        $eventSchemaPath = Join-Path $governanceRoot 'schemas\governance-event.schema.json'
        foreach ($jsonPath in @($manifestPath, $stateDataPath, $stateSchemaPath, $eventSchemaPath)) {
            try {
                Get-Content -LiteralPath $jsonPath -Raw | ConvertFrom-Json | Out-Null
            }
            catch {
                Add-ValidationError "Invalid JSON: $($jsonPath.Substring($resolvedRoot.Length + 1)) - $($_.Exception.Message)"
            }
        }
    }
    catch {
        Add-ValidationError "Unable to parse manifest: $($_.Exception.Message)"
    }
}

if ($script:ValidationErrors.Count -gt 0) {
    Write-Host 'FAIL: PolyNexus SOP v1.1 governance validation failed.' -ForegroundColor Red
    $script:ValidationErrors | ForEach-Object { Write-Host "- $_" }
    exit 1
}

Write-Host 'PASS: PolyNexus SOP v1.1 governance files, manifest, JSON and protected-path exclusions are valid.' -ForegroundColor Green
Write-Host 'INFO: This read-only check validates the additive package only; target-repo FVS/ADR diff remains a required post-apply check.' -ForegroundColor Yellow
exit 0
