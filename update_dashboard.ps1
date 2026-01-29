#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Automated Market Ritual Dashboard Update Script
    
.DESCRIPTION
    Runs market ritual, converts to JSON, and pushes to GitHub for dashboard update
    
.PARAMETER Mode
    Specify 'premarket' or 'postmarket' (default: auto-detect)
    
.EXAMPLE
    .\update_dashboard.ps1
    .\update_dashboard.ps1 -Mode postmarket
#>

param(
    [ValidateSet('premarket', 'postmarket', 'auto')]
    [string]$Mode = 'auto'
)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host " Market Ritual Dashboard Auto-Update" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Get current directory
$scriptDir = $PSScriptRoot
Set-Location $scriptDir

# Step 1: Run Market Ritual
Write-Host "[1/4] Running market ritual..." -ForegroundColor Yellow

try {
    if ($Mode -eq 'auto') {
        & .\.venv\Scripts\python.exe market_ritual.py
    } else {
        & .\.venv\Scripts\python.exe market_ritual.py --$Mode
    }
    
    if ($LASTEXITCODE -ne 0) {
        throw "Market ritual script failed"
    }
    
    Write-Host "      ✓ Market ritual completed" -ForegroundColor Green
} catch {
    Write-Host "      ✗ Error running market ritual: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Step 2: Convert to JSON
Write-Host "[2/4] Converting to JSON..." -ForegroundColor Yellow

try {
    & .\.venv\Scripts\python.exe convert_to_json.py
    
    if ($LASTEXITCODE -ne 0) {
        throw "JSON conversion failed"
    }
    
    Write-Host "      ✓ JSON conversion completed" -ForegroundColor Green
} catch {
    Write-Host "      ✗ Error converting to JSON: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Step 3: Git Add & Commit
Write-Host "[3/4] Committing changes..." -ForegroundColor Yellow

try {
    Set-Location dashboard
    
    # Check if there are changes
    $status = git status --porcelain
    
    if ([string]::IsNullOrWhiteSpace($status)) {
        Write-Host "      → No changes to commit" -ForegroundColor Yellow
        Set-Location ..
        Write-Host ""
        Write-Host "========================================" -ForegroundColor Cyan
        Write-Host " Dashboard is already up to date!" -ForegroundColor Cyan
        Write-Host "========================================" -ForegroundColor Cyan
        Write-Host ""
        exit 0
    }
    
    git add data/*.json
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $commitMsg = "Auto-update: Market data $timestamp CST"
    
    git commit -m $commitMsg
    
    Write-Host "      ✓ Changes committed" -ForegroundColor Green
} catch {
    Write-Host "      ✗ Error committing changes: $_" -ForegroundColor Red
    Set-Location ..
    exit 1
}

Write-Host ""

# Step 4: Push to GitHub
Write-Host "[4/4] Pushing to GitHub..." -ForegroundColor Yellow

try {
    git push
    
    if ($LASTEXITCODE -ne 0) {
        throw "Git push failed"
    }
    
    Write-Host "      ✓ Pushed to GitHub" -ForegroundColor Green
} catch {
    Write-Host "      ✗ Error pushing to GitHub: $_" -ForegroundColor Red
    Write-Host "      → Make sure you're authenticated and have push access" -ForegroundColor Yellow
    Set-Location ..
    exit 1
}

Set-Location ..

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host " ✓ Dashboard Updated Successfully!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Your dashboard will update in 2-3 minutes at:" -ForegroundColor Cyan
Write-Host "https://aladinz.github.io/daily_market_ritual/" -ForegroundColor White
Write-Host ""
