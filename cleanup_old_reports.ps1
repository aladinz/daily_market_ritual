#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Clean up old market ritual reports
    
.DESCRIPTION
    Keeps recent reports and archives or deletes older ones to prevent folder bloat
    
.PARAMETER DaysToKeep
    Number of days of reports to keep (default: 30)
    
.PARAMETER Archive
    If set, moves old reports to archive folder instead of deleting
    
.EXAMPLE
    .\cleanup_old_reports.ps1
    .\cleanup_old_reports.ps1 -DaysToKeep 60
    .\cleanup_old_reports.ps1 -DaysToKeep 30 -Archive
#>

param(
    [int]$DaysToKeep = 30,
    [switch]$Archive
)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host " Market Ritual Cleanup Utility" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Settings:" -ForegroundColor Yellow
Write-Host "  • Keep reports from last $DaysToKeep days" -ForegroundColor White
Write-Host "  • Action: $(if ($Archive) { 'Archive to backup folder' } else { 'Permanently delete' })" -ForegroundColor White
Write-Host ""

$scriptDir = $PSScriptRoot
Set-Location $scriptDir

$cutoffDate = (Get-Date).AddDays(-$DaysToKeep)
$folders = @("rituals\premarket", "rituals\postmarket")

$totalDeleted = 0
$totalArchived = 0

foreach ($folder in $folders) {
    Write-Host "Processing $folder..." -ForegroundColor Yellow
    
    # Get all summary files (exclude latest.txt)
    $files = Get-ChildItem "$folder\summary_*.txt" -ErrorAction SilentlyContinue
    
    if (-not $files) {
        Write-Host "  → No old reports found" -ForegroundColor Gray
        continue
    }
    
    $oldFiles = $files | Where-Object { $_.LastWriteTime -lt $cutoffDate }
    
    if ($oldFiles.Count -eq 0) {
        Write-Host "  → All reports are within retention period" -ForegroundColor Green
        continue
    }
    
    Write-Host "  → Found $($oldFiles.Count) old reports" -ForegroundColor White
    
    if ($Archive) {
        # Create archive folder
        $archiveFolder = Join-Path $folder "archive"
        if (-not (Test-Path $archiveFolder)) {
            New-Item -ItemType Directory -Path $archiveFolder | Out-Null
            Write-Host "  → Created archive folder" -ForegroundColor Cyan
        }
        
        # Move old files to archive
        foreach ($file in $oldFiles) {
            Move-Item -Path $file.FullName -Destination $archiveFolder -Force
            $totalArchived++
        }
        
        Write-Host "  ✓ Archived $($oldFiles.Count) reports" -ForegroundColor Green
    } else {
        # Delete old files
        foreach ($file in $oldFiles) {
            Remove-Item -Path $file.FullName -Force
            $totalDeleted++
        }
        
        Write-Host "  ✓ Deleted $($oldFiles.Count) reports" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host " ✓ Cleanup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

if ($Archive) {
    Write-Host "Archived: $totalArchived old reports" -ForegroundColor Cyan
    Write-Host "Kept: Reports from last $DaysToKeep days + latest.txt" -ForegroundColor Cyan
} else {
    Write-Host "Deleted: $totalDeleted old reports" -ForegroundColor Cyan
    Write-Host "Kept: Reports from last $DaysToKeep days + latest.txt" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "Tip: Add this to your scheduled tasks to run monthly!" -ForegroundColor Yellow
Write-Host ""
