param(
    [string]$LogPath,
    [string]$ArchiveRoot,
    [switch]$CopyOnly,
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

if (-not $ArchiveRoot) {
    $ArchiveRoot = Join-Path (Split-Path -Parent $LogPath) "archive"
}

$ArchiveRoot = [System.IO.Path]::GetFullPath($ArchiveRoot)

if (-not (Test-Path -LiteralPath $LogPath -PathType Leaf)) {
    Write-Host "No log to archive: $LogPath"
    exit 0
}

$logItem = Get-Item -LiteralPath $LogPath
if ($logItem.Length -le 0) {
    Write-Host "Log exists but is empty: $LogPath"
    exit 0
}

$lastWrite = $logItem.LastWriteTime
$stamp = $lastWrite.ToString("yyyyMMdd_HHmmss")
$archiveDir = Join-Path $ArchiveRoot $lastWrite.ToString("yyyy-MM")
$hash = (Get-FileHash -LiteralPath $LogPath -Algorithm SHA256).Hash.ToLowerInvariant()
$hashShort = $hash.Substring(0, 12)
$baseName = [System.IO.Path]::GetFileNameWithoutExtension($logItem.Name)
$extension = [System.IO.Path]::GetExtension($logItem.Name)

New-Item -ItemType Directory -Path $archiveDir -Force | Out-Null

$archiveName = "{0}_{1}_{2}{3}" -f $baseName, $stamp, $hashShort, $extension
$archivePath = Join-Path $archiveDir $archiveName
$counter = 1
while (Test-Path -LiteralPath $archivePath) {
    $archiveName = "{0}_{1}_{2}_{3}{4}" -f $baseName, $stamp, $hashShort, $counter, $extension
    $archivePath = Join-Path $archiveDir $archiveName
    $counter += 1
}

if ($CopyOnly) {
    Copy-Item -LiteralPath $LogPath -Destination $archivePath
} else {
    Move-Item -LiteralPath $LogPath -Destination $archivePath
}

$summarizer = Resolve-Summarizer
$summaryTextPath = "$archivePath.summary.txt"
$summaryJsonPath = "$archivePath.summary.json"
$summaryError = $null

if ($summarizer) {
    try {
        $summaryText = & python $summarizer $archivePath
        $summaryJson = & python $summarizer --json $archivePath
        $summaryText | Set-Content -LiteralPath $summaryTextPath -Encoding utf8
        $summaryJson | Set-Content -LiteralPath $summaryJsonPath -Encoding utf8
    } catch {
        $summaryError = $_.Exception.Message
    }
}

$metadata = [ordered]@{
    archived_at       = (Get-Date).ToString("o")
    mode              = $(if ($CopyOnly) { "copy" } else { "move" })
    original_path     = $logItem.FullName
    archive_path      = $archivePath
    size_bytes        = [int64]$logItem.Length
    last_write_time   = $lastWrite.ToString("o")
    sha256            = $hash
    summarizer_path   = $summarizer
    summary_text_path = $(if ((Test-Path -LiteralPath $summaryTextPath -PathType Leaf)) { $summaryTextPath } else { $null })
    summary_json_path = $(if ((Test-Path -LiteralPath $summaryJsonPath -PathType Leaf)) { $summaryJsonPath } else { $null })
    summary_error     = $summaryError
}

$metadataPath = "$archivePath.json"
$metadata | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $metadataPath -Encoding utf8

if ($TouchNewLog -and -not $CopyOnly) {
    New-Item -ItemType File -Path $LogPath -Force | Out-Null
}

Write-Host "Archived Tera Term log:"
Write-Host "  from: $($logItem.FullName)"
Write-Host "  to:   $archivePath"
Write-Host "  sha:  $hash"
if (Test-Path -LiteralPath $summaryTextPath -PathType Leaf) {
    Write-Host "  sum:  $summaryTextPath"
}
if (Test-Path -LiteralPath $summaryJsonPath -PathType Leaf) {
    Write-Host "  json: $summaryJsonPath"
}
if ($TouchNewLog -and -not $CopyOnly) {
    Write-Host "  new:  $LogPath"
}
