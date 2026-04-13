param(
    [string]$LogPath,
    [switch]$TouchNewLog
)

$ErrorActionPreference = "Stop"

function Resolve-RepoRoot {
    return (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
}

function Resolve-Summarizer {
    $repoRoot = Resolve-RepoRoot
    $candidates = @(
        (Join-Path $repoRoot "build\summarize_teraterm_boot.py"),
        "D:\Projects\porta-a733-bringup\build\summarize_teraterm_boot.py"
    )

    foreach ($candidate in $candidates) {
        if (Test-Path -LiteralPath $candidate -PathType Leaf) {
            return [System.IO.Path]::GetFullPath($candidate)
        }
    }

    return $null
}

if (-not $LogPath) {
    $LogPath = Join-Path (Resolve-RepoRoot) "log\teraterm.log"
}

$LogPath = [System.IO.Path]::GetFullPath($LogPath)

if (-not (Test-Path -LiteralPath $LogPath -PathType Leaf)) {
    Write-Host "No log to finalize: $LogPath"
    exit 0
}

$logItem = Get-Item -LiteralPath $LogPath
if ($logItem.Length -le 0) {
    Write-Host "Log exists but is empty: $LogPath"
    exit 0
}

$logDir = Split-Path -Parent $LogPath
$stamp = $logItem.LastWriteTime.ToString("yyyy-MM-dd_HHmmss")
$targetBase = "teraterm_{0}" -f $stamp
$targetPath = Join-Path $logDir ($targetBase + ".log")
$counter = 1
while (Test-Path -LiteralPath $targetPath) {
    $targetPath = Join-Path $logDir ("{0}_{1}.log" -f $targetBase, $counter)
    $counter += 1
}

Move-Item -LiteralPath $LogPath -Destination $targetPath

$summaryTextPath = "$targetPath.summary.txt"
$summaryJsonPath = "$targetPath.summary.json"
$summarizer = Resolve-Summarizer

if ($summarizer) {
    & python $summarizer $targetPath | Set-Content -LiteralPath $summaryTextPath -Encoding utf8
    & python $summarizer --json $targetPath | Set-Content -LiteralPath $summaryJsonPath -Encoding utf8
}

if ($TouchNewLog) {
    New-Item -ItemType File -Path $LogPath -Force | Out-Null
}

Write-Host "Finalized Tera Term log:"
Write-Host "  from: $($logItem.FullName)"
Write-Host "  to:   $targetPath"
if (Test-Path -LiteralPath $summaryTextPath -PathType Leaf) {
    Write-Host "  sum:  $summaryTextPath"
}
if (Test-Path -LiteralPath $summaryJsonPath -PathType Leaf) {
    Write-Host "  json: $summaryJsonPath"
}
if ($TouchNewLog) {
    Write-Host "  new:  $LogPath"
}
