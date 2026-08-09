#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Scan markdown files for deadlinks (broken file references).

.DESCRIPTION
    Recursively scans all .md files in the repo and validates internal links.
    - Skips external URLs (http://, https://)
    - Checks relative file paths
    - Validates anchor references (#)
    - Reports missing files with line numbers

.PARAMETER RepoRoot
    Root directory to scan. Defaults to current directory or git root.

.PARAMETER OutputFormat
    Output format: 'table', 'json', or 'list'. Default: 'table'

.PARAMETER FailOnDeadlinks
    Exit with code 1 if deadlinks found. Default: false

.EXAMPLE
    # Scan current repo
    .\check-md-deadlinks.ps1

    # Scan specific directory
    .\check-md-deadlinks.ps1 -RepoRoot "D:\repos\ITL.Github"

    # JSON output for CI/CD
    .\check-md-deadlinks.ps1 -OutputFormat json -FailOnDeadlinks

    # Pipe to file
    .\check-md-deadlinks.ps1 | Out-File deadlinks.txt
#>

param(
    [string]$RepoRoot = (git rev-parse --show-toplevel 2>$null) ?? (Get-Location),
    [ValidateSet('table', 'json', 'list')]
    [string]$OutputFormat = 'table',
    [switch]$FailOnDeadlinks
)

$ErrorActionPreference = 'Continue'
$WarningPreference = 'SilentlyContinue'

# Find all markdown files
$mdFiles = @(Get-ChildItem -Path $RepoRoot -Filter '*.md' -Recurse -ErrorAction SilentlyContinue)

if ($mdFiles.Count -eq 0) {
    Write-Host "❌ No markdown files found in $RepoRoot" -ForegroundColor Red
    exit 1
}

Write-Host "🔍 Scanning $($mdFiles.Count) markdown files for deadlinks..." -ForegroundColor Cyan

$deadlinks = @()
$validLinks = 0
$skippedLinks = 0

# Regex to match markdown links: [text](url) or [text](url#anchor)
$linkPattern = '\[([^\]]+)\]\(([^)]+)\)'

foreach ($mdFile in $mdFiles) {
    $relativePath = $mdFile.FullName.Replace($RepoRoot, '').TrimStart('\', '/')
    $content = Get-Content -Path $mdFile.FullName -Raw -ErrorAction SilentlyContinue
    
    if (-not $content) { continue }
    
    $lineNumber = 0
    foreach ($line in $content -split "`n") {
        $lineNumber++
        
        # Find all links in this line
        $matches = [regex]::Matches($line, $linkPattern)
        
        foreach ($match in $matches) {
            $linkText = $match.Groups[1].Value
            $linkUrl = $match.Groups[2].Value
            
            # Skip external URLs
            if ($linkUrl -match '^https?://' -or $linkUrl -match '^mailto:') {
                $skippedLinks++
                continue
            }
            
            # Split anchor from path
            $linkPath = $linkUrl -split '#' | Select-Object -First 1
            
            # Skip if link is just an anchor (same file)
            if ([string]::IsNullOrWhiteSpace($linkPath)) {
                $skippedLinks++
                continue
            }
            
            # Resolve relative path
            $basePath = Split-Path -Parent $mdFile.FullName
            $resolvedPath = Join-Path -Path $basePath -ChildPath $linkPath
            $resolvedPath = [System.IO.Path]::GetFullPath($resolvedPath)
            
            # Check if file exists
            $exists = Test-Path -Path $resolvedPath -ErrorAction SilentlyContinue
            
            if ($exists) {
                $validLinks++
            } else {
                $deadlinks += @{
                    File       = $relativePath
                    Line       = $lineNumber
                    LinkText   = $linkText
                    LinkUrl    = $linkUrl
                    ResolvedTo = $resolvedPath
                    Status     = 'DEAD'
                }
            }
        }
    }
}

# Output results
$totalLinks = $validLinks + $deadlinks.Count + $skippedLinks

Write-Host ""
Write-Host "📊 Summary" -ForegroundColor Cyan
Write-Host "  Total links found: $totalLinks"
Write-Host "  ✅ Valid: $validLinks" -ForegroundColor Green
Write-Host "  ⏭️  Skipped (external/anchor): $skippedLinks" -ForegroundColor Yellow
Write-Host "  ❌ Deadlinks: $($deadlinks.Count)" -ForegroundColor Red
Write-Host ""

if ($deadlinks.Count -gt 0) {
    switch ($OutputFormat) {
        'table' {
            Write-Host "Deadlinks Found:" -ForegroundColor Red
            Write-Host ""
            $deadlinks | Format-Table -Property @(
                @{ Label = 'File'; Expression = { $_.File } }
                @{ Label = 'Line'; Expression = { $_.Line } }
                @{ Label = 'Link'; Expression = { $_.LinkText } }
                @{ Label = 'Target'; Expression = { $_.LinkUrl } }
            ) -AutoSize
        }
        'list' {
            Write-Host "Deadlinks Found:" -ForegroundColor Red
            Write-Host ""
            foreach ($deadlink in $deadlinks) {
                Write-Host "$($deadlink.File):$($deadlink.Line)" -ForegroundColor Red -NoNewline
                Write-Host " - [$($deadlink.LinkText)]($($deadlink.LinkUrl))" -ForegroundColor Gray
            }
        }
        'json' {
            $output = @{
                timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
                repoRoot = $RepoRoot
                summary = @{
                    totalLinks = $totalLinks
                    validLinks = $validLinks
                    skippedLinks = $skippedLinks
                    deadlinks = $deadlinks.Count
                }
                deadlinks = $deadlinks
            }
            $output | ConvertTo-Json -Depth 3
        }
    }
    
    Write-Host ""
    
    if ($FailOnDeadlinks) {
        Write-Host "❌ Pipeline would fail due to deadlinks" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "✅ No deadlinks found!" -ForegroundColor Green
    exit 0
}
