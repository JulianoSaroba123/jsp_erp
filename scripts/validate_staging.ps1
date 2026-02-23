#!/usr/bin/env pwsh
# ===================================================================
# VALIDADOR DE STAGING - ERP JSP
# ===================================================================
# Valida deploy no Render via health check e smoke test automatizado
#
# Uso:
#   .\validate_staging.ps1
#   .\validate_staging.ps1 -Verbose
#   .\validate_staging.ps1 -BaseUrl "https://custom-domain.com"
# ===================================================================

param(
    [string]$BaseUrl = "https://jsp-erp-backend.onrender.com",
    [switch]$Verbose
)

$ErrorActionPreference = "Stop"

# Cores
function Write-Success { param($msg) Write-Host "✅ $msg" -ForegroundColor Green }
function Write-Error-Custom { param($msg) Write-Host "❌ $msg" -ForegroundColor Red }
function Write-Info { param($msg) Write-Host "ℹ️  $msg" -ForegroundColor Cyan }
function Write-Warning-Custom { param($msg) Write-Host "⚠️  $msg" -ForegroundColor Yellow }

# Banner
Write-Host ""
Write-Host "═════════════════════════════════════════" -ForegroundColor Magenta
Write-Host "  🧪 VALIDAÇÃO DE STAGING - ERP JSP" -ForegroundColor Magenta
Write-Host "═════════════════════════════════════════" -ForegroundColor Magenta
Write-Info "Target: $BaseUrl"
Write-Info "Time: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Host ""

$results = @{
    health = $false
    docs = $false
    redoc = $false
    smoke_test = $false
}

# ===================================================================
# TEST 1: Health Check
# ===================================================================
Write-Host "TEST 1/4: Health Check" -ForegroundColor Yellow
Write-Host "─────────────────────────────────────────"

try {
    $healthUrl = "$BaseUrl/health"
    Write-Info "GET $healthUrl"
    
    $response = Invoke-WebRequest -Uri $healthUrl -Method GET -UseBasicParsing -TimeoutSec 30
    
    if ($response.StatusCode -eq 200) {
        $body = $response.Content | ConvertFrom-Json
        
        if ($Verbose) {
            Write-Host "Response:" -ForegroundColor Gray
            Write-Host ($body | ConvertTo-Json -Depth 3) -ForegroundColor Gray
        }
        
        if ($body.ok -eq $true) {
            Write-Success "Health check OK"
            Write-Info "  Service: $($body.service)"
            Write-Info "  Environment: $($body.env)"
            Write-Info "  Database: $($body.database)"
            
            if ($body.database -eq "healthy") {
                $results.health = $true
            } else {
                Write-Error-Custom "Database status: $($body.database)"
            }
        } else {
            Write-Error-Custom "Health check returned ok=false"
        }
    } else {
        Write-Error-Custom "HTTP $($response.StatusCode)"
    }
} catch {
    Write-Error-Custom "Failed to reach health endpoint"
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""

# ===================================================================
# TEST 2: Swagger UI (/docs)
# ===================================================================
Write-Host "TEST 2/4: Swagger UI" -ForegroundColor Yellow
Write-Host "─────────────────────────────────────────"

try {
    $docsUrl = "$BaseUrl/docs"
    Write-Info "GET $docsUrl"
    
    $response = Invoke-WebRequest -Uri $docsUrl -Method GET -UseBasicParsing -TimeoutSec 30
    
    if ($response.StatusCode -eq 200) {
        if ($response.Content -match "swagger-ui") {
            Write-Success "Swagger UI accessible"
            $results.docs = $true
        } else {
            Write-Warning-Custom "Response doesn't contain Swagger UI"
        }
    } else {
        Write-Error-Custom "HTTP $($response.StatusCode)"
    }
} catch {
    Write-Error-Custom "Failed to reach /docs"
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""

# ===================================================================
# TEST 3: ReDoc UI (/redoc)
# ===================================================================
Write-Host "TEST 3/4: ReDoc UI" -ForegroundColor Yellow
Write-Host "─────────────────────────────────────────"

try {
    $redocUrl = "$BaseUrl/redoc"
    Write-Info "GET $redocUrl"
    
    $response = Invoke-WebRequest -Uri $redocUrl -Method GET -UseBasicParsing -TimeoutSec 30
    
    if ($response.StatusCode -eq 200) {
        if ($response.Content -match "redoc") {
            Write-Success "ReDoc accessible"
            $results.redoc = $true
        } else {
            Write-Warning-Custom "Response doesn't contain ReDoc"
        }
    } else {
        Write-Error-Custom "HTTP $($response.StatusCode)"
    }
} catch {
    Write-Error-Custom "Failed to reach /redoc"
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""

# ===================================================================
# TEST 4: Smoke Test E2E (Python script)
# ===================================================================
Write-Host "TEST 4/4: Smoke Test E2E" -ForegroundColor Yellow
Write-Host "─────────────────────────────────────────"

$scriptsDir = Split-Path -Parent $PSScriptRoot
$smokeTestPath = Join-Path $scriptsDir "scripts\smoke_test_staging.py"

if (Test-Path $smokeTestPath) {
    Write-Info "Running: python smoke_test_staging.py"
    
    try {
        $env:STAGING_BASE_URL = $BaseUrl
        
        $smokeTestOutput = & python $smokeTestPath 2>&1
        $smokeTestExitCode = $LASTEXITCODE
        
        if ($Verbose) {
            Write-Host "Output:" -ForegroundColor Gray
            $smokeTestOutput | ForEach-Object { Write-Host $_ -ForegroundColor Gray }
        }
        
        if ($smokeTestExitCode -eq 0) {
            Write-Success "Smoke test passed (5/5)"
            $results.smoke_test = $true
        } else {
            Write-Error-Custom "Smoke test failed (exit code: $smokeTestExitCode)"
            if (-not $Verbose) {
                Write-Warning-Custom "Run with -Verbose to see detailed output"
            }
        }
    } catch {
        Write-Error-Custom "Failed to run smoke test"
        Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    }
} else {
    Write-Warning-Custom "Smoke test script not found at: $smokeTestPath"
    Write-Info "Skipping E2E tests"
}

Write-Host ""

# ===================================================================
# SUMMARY
# ===================================================================
Write-Host "═════════════════════════════════════════" -ForegroundColor Magenta
Write-Host "  📊 SUMMARY" -ForegroundColor Magenta
Write-Host "═════════════════════════════════════════" -ForegroundColor Magenta

$passed = ($results.Values | Where-Object { $_ -eq $true }).Count
$total = $results.Count

Write-Host ""
foreach ($test in $results.GetEnumerator()) {
    $status = if ($test.Value) { "✅ PASS" } else { "❌ FAIL" }
    $color = if ($test.Value) { "Green" } else { "Red" }
    Write-Host ("{0,-20} {1}" -f $test.Key, $status) -ForegroundColor $color
}

Write-Host ""
Write-Host "─────────────────────────────────────────"

if ($passed -eq $total) {
    Write-Host "✅ ALL TESTS PASSED ($passed/$total)" -ForegroundColor Green
    Write-Host ""
    Write-Host "🎉 STAGING IS READY!" -ForegroundColor Green -BackgroundColor DarkGreen
    Write-Host ""
    exit 0
} else {
    Write-Host "❌ SOME TESTS FAILED ($passed/$total)" -ForegroundColor Red
    Write-Host ""
    Write-Host "🚨 Staging NOT ready - check logs" -ForegroundColor Red -BackgroundColor DarkRed
    Write-Host ""
    Write-Warning-Custom "Troubleshooting guide: RUNBOOK_DEPLOY_RENDER.md"
    exit 1
}
