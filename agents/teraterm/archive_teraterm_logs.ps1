param(
    [string]$LogDir,
    [string]$ArchiveRoot,
    [switch]$TouchNewCurrentLog
)

$ErrorActionPreference = "Stop"

function Resolve-RepoRoot {
    return (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
}

$singleScript = Join-Path $PSScriptRoot "archive_teraterm_log.ps1"
if (-not (Test-Path -LiteralPath $singleScript -PathType Leaf)) {
    throw "Missing helper script: $singleScript"
}

if (-not $LogDir) {
    $LogDir = Join-Path (Resolve-RepoRoot) "log"
}

$LogDir = [System.IO.Path]::GetFullPath($LogDir)

if (-not $ArchiveRoot) {
    $ArchiveRoot = Join-Path $LogDir "archive"
}

$ArchiveRoot = [System.IO.Path]::GetFullPath($ArchiveRoot)

if (-not (Test-Path -LiteralPath $LogDir -PathType Container)) {
    throw "Log directory not found: $LogDir"
}

$logs = Get-ChildItem -LiteralPath $LogDir -File |
    Where-Object { $_.Name -match '^teraterm.*\.log$' } |
    Sort-Object LastWriteTime, Name

if (-not $logs) {
    Write-Host "No Tera Term logs found in: $LogDir"
    exit 0
}

$count = 0
foreach ($log in $logs) {
    $params = @{
        LogPath     = $log.FullName
        ArchiveRoot = $ArchiveRoot
    }
    if ($TouchNewCurrentLog -and $log.Name -ieq "teraterm.log") {
        $params.TouchNewLog = $true
    }
    & $singleScript @params
    $count += 1
}

Write-Host ""
Write-Host "Archived $count Tera Term log file(s) from: $LogDir"
Write-Host "Archive root: $ArchiveRoot"
