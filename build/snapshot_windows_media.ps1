param(
    [string]$Root = "F:\",
    [string]$Output
)

$ErrorActionPreference = "Stop"

function Normalize-RootPath {
    param([string]$PathText)
    if ([string]::IsNullOrWhiteSpace($PathText)) {
        throw "Root path is empty"
    }
    $full = [System.IO.Path]::GetFullPath($PathText)
    if (-not (Test-Path -LiteralPath $full)) {
        throw "Root path not found: $full"
    }
    return $full.TrimEnd('\')
}

function Resolve-OutputPath {
    param(
        [string]$Requested,
        [string]$NormalizedRoot
    )

    if (-not [string]::IsNullOrWhiteSpace($Requested)) {
        $parent = Split-Path -Parent $Requested
        if ($parent) {
            New-Item -ItemType Directory -Force -Path $parent | Out-Null
        }
        return $Requested
    }

    $stamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $defaultDir = "D:\Projects\porta-a733-bringup\analysis\media_snapshots"
    New-Item -ItemType Directory -Force -Path $defaultDir | Out-Null
    $leaf = ($NormalizedRoot -replace "[:\\\/]+", "_").Trim("_")
    if (-not $leaf) {
        $leaf = "root"
    }
    return (Join-Path $defaultDir "windows_media_${leaf}_${stamp}.md")
}

function Get-FileSection {
    param(
        [string]$RootPath,
        [string]$RelativePath
    )

    $fullPath = Join-Path $RootPath $RelativePath
    $lines = New-Object System.Collections.Generic.List[string]
    $lines.Add("## $RelativePath")
    $lines.Add("")

    if (-not (Test-Path -LiteralPath $fullPath)) {
        $lines.Add("- status: missing")
        $lines.Add("")
        return @{
            Lines = $lines
            Exists = $false
            Hash = $null
        }
    }

    $item = Get-Item -LiteralPath $fullPath
    $hash = (Get-FileHash -Algorithm SHA256 -LiteralPath $fullPath).Hash

    $lines.Add("- status: present")
    $lines.Add("- full_path: $fullPath")
    $lines.Add("- length: $($item.Length)")
    $lines.Add("- last_write_time: $($item.LastWriteTime.ToString("yyyy-MM-dd HH:mm:ss"))")
    $lines.Add("- sha256: $hash")

    $extension = $item.Extension.ToLowerInvariant()
    if ($extension -in @(".txt", ".nsh", ".md")) {
        $lines.Add("- preview:")
        $lines.Add("")
        $lines.Add("~~~text")
        Get-Content -LiteralPath $fullPath -Encoding UTF8 -ErrorAction SilentlyContinue | Select-Object -First 40 | ForEach-Object {
            $lines.Add($_)
        }
        $lines.Add("~~~")
    }

    $lines.Add("")
    return @{
        Lines = $lines
        Exists = $true
        Hash = $hash
    }
}

function Get-ClassifierSection {
    param(
        [string]$RootPath,
        [hashtable]$Results
    )

    $lines = New-Object System.Collections.Generic.List[string]
    $targetPath = Join-Path $RootPath "EFI\BOOT\BOOTAA64.EFI"
    if (-not (Test-Path -LiteralPath $targetPath)) {
        return $lines
    }

    $python = Get-Command python -ErrorAction SilentlyContinue
    if (-not $python) {
        return $lines
    }

    $classifier = "D:\Projects\porta-a733-bringup\build\classify_bootaa64_state.py"
    $original = "D:\Projects\porta-a733-bringup\build\BOOTAA64.original.EFI"
    $fixed = "D:\Projects\porta-a733-bringup\build\BOOTAA64.fixed.EFI"
    $patchScript = "D:\Projects\porta-a733-bringup\build\patch_bootaa64.py"
    $markerPath = Join-Path $RootPath "EFI\BOOT\BOOTAA64.PATCH.txt"

    if (-not (Test-Path -LiteralPath $classifier) -or -not (Test-Path -LiteralPath $original)) {
        return $lines
    }

    $args = @(
        $classifier,
        $targetPath,
        "--original", $original
    )
    if (Test-Path -LiteralPath $fixed) {
        $args += @("--fixed", $fixed)
    }
    if (Test-Path -LiteralPath $patchScript) {
        $args += @("--patch-script", $patchScript)
    }
    if (Test-Path -LiteralPath $markerPath) {
        $args += @("--marker", $markerPath)
    }

    $output = & $python.Source @args 2>&1
    $exitCode = $LASTEXITCODE
    $lines.Add("## BOOTAA64 Classification")
    $lines.Add("")
    if ($exitCode -ne 0) {
        $lines.Add("- status: classifier failed")
        $lines.Add("- exit_code: $exitCode")
        $lines.Add("")
        $lines.Add("~~~text")
        foreach ($line in $output) {
            $lines.Add([string]$line)
        }
        $lines.Add("~~~")
        $lines.Add("")
        return $lines
    }

    $lines.Add("~~~text")
    foreach ($line in $output) {
        $lines.Add([string]$line)
    }
    $lines.Add("~~~")
    $lines.Add("")

    $markerHash = $null
    if ($Results.ContainsKey("EFI\BOOT\BOOTAA64.PATCH.txt") -and $Results["EFI\BOOT\BOOTAA64.PATCH.txt"].Exists) {
        $markerFullPath = Join-Path $RootPath "EFI\BOOT\BOOTAA64.PATCH.txt"
        $markerText = Get-Content -LiteralPath $markerFullPath -Raw -Encoding UTF8 -ErrorAction SilentlyContinue
        if ($markerText) {
            $match = [regex]::Match($markerText, '(?m)^BOOTAA64_SHA256=([0-9A-Fa-f]{64})$')
            if ($match.Success) {
                $markerHash = $match.Groups[1].Value.ToUpperInvariant()
            }
        }
    }

    $bootHash = $Results["EFI\BOOT\BOOTAA64.EFI"].Hash
    if ($bootHash -and $markerHash) {
        if ($bootHash -eq $markerHash) {
            $lines.Add("- marker hash matches current BOOTAA64.EFI")
        } else {
            $lines.Add("- marker hash does not match current BOOTAA64.EFI")
        }
        $lines.Add("")
    }
    return $lines
}

$normalizedRoot = Normalize-RootPath -PathText $Root
$outputPath = Resolve-OutputPath -Requested $Output -NormalizedRoot $normalizedRoot

$targets = @(
    "EFI\BOOT\BOOTAA64.EFI",
    "EFI\Microsoft\Boot\bootmgfw.efi",
    "EFI\BOOT\BOOTAA64.PATCH.txt",
    "startup.nsh",
    "EFI\Microsoft\Boot\BCD"
)

$report = New-Object System.Collections.Generic.List[string]
$report.Add("# Windows Media Snapshot")
$report.Add("")
$report.Add("- root: $normalizedRoot")
$report.Add("- captured_at: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")")
$report.Add("")

$results = @{}
foreach ($target in $targets) {
    $section = Get-FileSection -RootPath $normalizedRoot -RelativePath $target
    $results[$target] = $section
    foreach ($line in $section.Lines) {
        $report.Add($line)
    }
}

foreach ($line in (Get-ClassifierSection -RootPath $normalizedRoot -Results $results)) {
    $report.Add($line)
}

$bootHash = $results["EFI\BOOT\BOOTAA64.EFI"].Hash
$bootmgfwHash = $results["EFI\Microsoft\Boot\bootmgfw.efi"].Hash
$markerPresent = $results["EFI\BOOT\BOOTAA64.PATCH.txt"].Exists

$report.Add("## Summary")
$report.Add("")
if ($bootHash -and $bootmgfwHash) {
    if ($bootHash -eq $bootmgfwHash) {
        $report.Add("- BOOTAA64.EFI and bootmgfw.efi hashes match")
    } else {
        $report.Add("- BOOTAA64.EFI and bootmgfw.efi hashes differ")
    }
}
if ($markerPresent) {
    $report.Add("- BOOTAA64.PATCH.txt is present")
} else {
    $report.Add("- BOOTAA64.PATCH.txt is absent")
}
if ($markerPresent -and $bootHash) {
    $markerFullPath = Join-Path $normalizedRoot "EFI\BOOT\BOOTAA64.PATCH.txt"
    $markerText = Get-Content -LiteralPath $markerFullPath -Raw -Encoding UTF8 -ErrorAction SilentlyContinue
    if ($markerText) {
        $match = [regex]::Match($markerText, '(?m)^BOOTAA64_SHA256=([0-9A-Fa-f]{64})$')
        if ($match.Success) {
            $claimedHash = $match.Groups[1].Value.ToUpperInvariant()
            if ($claimedHash -eq $bootHash) {
                $report.Add("- BOOTAA64.PATCH.txt claimed hash matches BOOTAA64.EFI")
            } else {
                $report.Add("- BOOTAA64.PATCH.txt claimed hash does not match BOOTAA64.EFI")
            }
        }
    }
}
$report.Add("")

Set-Content -LiteralPath $outputPath -Value $report -Encoding UTF8
Write-Output "Wrote media snapshot: $outputPath"
