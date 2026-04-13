param(
    [string]$TargetRoot = "F:\",
    [string]$StageSourceEfi,
    [string]$PatchName,
    [string[]]$PatchVas,
    [ValidateSet("keep", "bootmgfw_only", "bootmgfw_then_bootaa64")]
    [string]$StartupMode = "bootmgfw_only",
    [switch]$SkipTeraTermArchive,
    [switch]$SkipPreSnapshot,
    [switch]$SkipPostSnapshot
)

$ErrorActionPreference = "Stop"

function Ensure-Tool {
    param([string]$PathText)
    if (-not (Test-Path -LiteralPath $PathText)) {
        throw "Missing required tool: $PathText"
    }
    return (Resolve-Path -LiteralPath $PathText).Path
}

function Format-PatchVaValue {
    param($Value)
    if ($null -eq $Value) {
        return $null
    }
    if ($Value -is [string]) {
        $text = $Value.Trim()
        if (-not $text) {
            return $null
        }
        if ($text -match '^0[xX][0-9A-Fa-f]+$') {
            return ('0x{0:X8}' -f ([Convert]::ToUInt32($text, 16)))
        }
        return ('0x{0:X8}' -f ([Convert]::ToUInt32($text, 10)))
    }
    return ('0x{0:X8}' -f ([uint32]$Value))
}

function Normalize-PatchVas {
    param([object[]]$Values)
    $normalized = @()
    foreach ($value in $Values) {
        if ($null -eq $value) {
            continue
        }
        if ($value -is [string]) {
            $parts = $value -split '[,\s]+' | Where-Object { $_ }
            foreach ($part in $parts) {
                $formatted = Format-PatchVaValue $part
                if ($formatted) {
                    $normalized += $formatted
                }
            }
        } else {
            $formatted = Format-PatchVaValue $value
            if ($formatted) {
                $normalized += $formatted
            }
        }
    }
    return $normalized
}

function Run-Logged {
    param(
        [string]$Label,
        [scriptblock]$Body
    )

    Write-Host ""
    Write-Host "== $Label =="
    & $Body
}

$repoRoot = "D:\Projects\porta-a733-bringup"
$runStamp = Get-Date -Format "yyyyMMdd_HHmmss"
$runDir = Join-Path $repoRoot "analysis\run_preps\$runStamp"
New-Item -ItemType Directory -Force -Path $runDir | Out-Null

$archiveScript = "D:\Projects\PortaRe0\software\agents\teraterm\archive_teraterm_logs.ps1"
$snapshotScript = Ensure-Tool (Join-Path $repoRoot "build\snapshot_windows_media.ps1")
$stageScript = Ensure-Tool (Join-Path $repoRoot "build\stage_windows_loader_variant.py")

$summary = New-Object System.Collections.Generic.List[string]
$summary.Add("# Windows Debug Run Prep")
$summary.Add("")
$summary.Add("- run_dir: $runDir")
$summary.Add("- target_root: $TargetRoot")
$summary.Add("- created_at: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")")
$summary.Add("")

if (-not $SkipTeraTermArchive -and (Test-Path -LiteralPath $archiveScript)) {
    Run-Logged -Label "Archive TeraTerm logs" -Body {
        & powershell -ExecutionPolicy Bypass -File $archiveScript -TouchNewCurrentLog
    }
    $summary.Add("- teraterm_archive: executed")
} elseif ($SkipTeraTermArchive) {
    $summary.Add("- teraterm_archive: skipped by option")
} else {
    $summary.Add("- teraterm_archive: helper missing")
}

if (-not $SkipPreSnapshot) {
    $preSnapshot = Join-Path $runDir "media_before.md"
    Run-Logged -Label "Snapshot media before staging" -Body {
        & powershell -ExecutionPolicy Bypass -File $snapshotScript -Root $TargetRoot -Output $preSnapshot
    }
    $summary.Add("- pre_snapshot: $preSnapshot")
} else {
    $summary.Add("- pre_snapshot: skipped by option")
}

if ($StageSourceEfi) {
    $normalizedPatchVas = Normalize-PatchVas $PatchVas
    $stageArgs = @(
        (Ensure-Tool $stageScript),
        "--target-root", $TargetRoot,
        "--source-efi", $StageSourceEfi,
        "--startup-mode", $StartupMode
    )
    if ($PatchName) {
        $stageArgs += @("--patch-name", $PatchName)
    }
    if ($normalizedPatchVas) {
        $stageArgs += @("--patch-vas")
        $stageArgs += $normalizedPatchVas
    }

    Run-Logged -Label "Stage loader variant" -Body {
        & python @stageArgs
    }
    $summary.Add("- staged_source_efi: $StageSourceEfi")
    if ($PatchName) {
        $summary.Add("- staged_patch_name: $PatchName")
    }
    if ($normalizedPatchVas) {
        $summary.Add("- staged_patch_vas: $($normalizedPatchVas -join ',')")
    }
    $summary.Add("- staged_startup_mode: $StartupMode")
} else {
    $summary.Add("- staged_source_efi: none")
}

if (-not $SkipPostSnapshot) {
    $postSnapshot = Join-Path $runDir "media_after.md"
    Run-Logged -Label "Snapshot media after staging" -Body {
        & powershell -ExecutionPolicy Bypass -File $snapshotScript -Root $TargetRoot -Output $postSnapshot
    }
    $summary.Add("- post_snapshot: $postSnapshot")
} else {
    $summary.Add("- post_snapshot: skipped by option")
}

$summary.Add("")
$summaryPath = Join-Path $runDir "run_prep_summary.md"
$summary | Set-Content -LiteralPath $summaryPath -Encoding UTF8

Write-Host ""
Write-Host "Prep complete."
Write-Host "  run_dir: $runDir"
Write-Host "  summary: $summaryPath"
