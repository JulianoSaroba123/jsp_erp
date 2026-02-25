# Validador simples de staging
param(
    [string]$BaseUrl = "https://jsp-erp-backend.onrender.com"
)

Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host " VALIDACAO STAGING - ERP JSP" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Target: $BaseUrl" -ForegroundColor Gray
Write-Host "Time: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Gray
Write-Host ""

$passed = 0
$total = 3

# TEST 1: Health
Write-Host "[1/3] Testing /health..." -NoNewline
try {
    $response = Invoke-WebRequest "$BaseUrl/health" -UseBasicParsing -TimeoutSec 30
    if ($response.StatusCode -eq 200) {
        $body = $response.Content | ConvertFrom-Json
        if ($body.ok -eq $true -and $body.database -eq "healthy") {
            Write-Host " PASS" -ForegroundColor Green
            Write-Host "      Service: $($body.service), Env: $($body.env)" -ForegroundColor Gray
            $passed++
        } else {
            Write-Host " FAIL (ok=$($body.ok), db=$($body.database))" -ForegroundColor Red
        }
    } else {
        Write-Host " FAIL (HTTP $($response.StatusCode))" -ForegroundColor Red
    }
} catch {
    Write-Host " ERROR" -ForegroundColor Red
    Write-Host "      $($_.Exception.Message)" -ForegroundColor Gray
}

# TEST 2: Swagger
Write-Host "[2/3] Testing /docs..." -NoNewline
try {
    $response = Invoke-WebRequest "$BaseUrl/docs" -UseBasicParsing -TimeoutSec 30
    if ($response.StatusCode -eq 200) {
        Write-Host " PASS" -ForegroundColor Green
        $passed++
    } else {
        Write-Host " FAIL (HTTP $($response.StatusCode))" -ForegroundColor Red
    }
} catch {
    Write-Host " ERROR" -ForegroundColor Red
    Write-Host "      $($_.Exception.Message)" -ForegroundColor Gray
}

# TEST 3: Smoke test
Write-Host "[3/3] Running smoke test..." -NoNewline
try {
    $env:STAGING_BASE_URL = $BaseUrl
    $smokeScript = Join-Path (Split-Path $PSScriptRoot) "scripts\smoke_test_staging.py"
    
    if (Test-Path $smokeScript) {
        $output = & python $smokeScript 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host " PASS" -ForegroundColor Green
            $passed++
        } else {
            Write-Host " FAIL (exit $LASTEXITCODE)" -ForegroundColor Red
        }
    } else {
        Write-Host " SKIP (script not found)" -ForegroundColor Yellow
    }
} catch {
    Write-Host " ERROR" -ForegroundColor Red
    Write-Host "      $($_.Exception.Message)" -ForegroundColor Gray
}

# Summary
Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host " RESULTADO: $passed/$total PASSED" -ForegroundColor $(if ($passed -eq $total) { "Green" } else { "Yellow" })
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

if ($passed -eq $total) {
    Write-Host "*** STAGING OK! ***" -ForegroundColor Green -BackgroundColor DarkGreen
    Write-Host ""
    exit 0
} else {
    Write-Host "*** STAGING COM PROBLEMAS ***" -ForegroundColor Red -BackgroundColor DarkRed
    Write-Host ""
    Write-Host "Troubleshooting:" -ForegroundColor Yellow
    Write-Host "1. Verifique se deploy foi feito: https://dashboard.render.com" -ForegroundColor Gray
    Write-Host "2. Aguarde cold start (60s) se free tier" -ForegroundColor Gray
    Write-Host "3. Veja logs no Render Dashboard" -ForegroundColor Gray
    Write-Host ""
    exit 1
}
