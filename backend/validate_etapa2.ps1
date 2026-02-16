# SCRIPT DE VALIDAÇÃO COMPLETA - ETAPA 2
# Execute linha por linha ou salve como validate_etapa2.ps1

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  VALIDAÇÃO ETAPA 2 - HARDENING COMPLETO" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# PRÉ-REQUISITO: API rodando
try {
    $health = curl.exe -s http://localhost:8000/health | ConvertFrom-Json
    if ($health.app -eq "ERP JSP") {
        Write-Host "✅ API respondendo: $($health.app) v$($health.version)" -ForegroundColor Green
    } else {
        throw "API não retornou resposta esperada"
    }
} catch {
    Write-Host "❌ API não está respondendo. Inicie com: python -m uvicorn app.main:app" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "TESTE 2: Login -> Obter Tokens" -ForegroundColor Yellow
Write-Host "==============================" -ForegroundColor Yellow

$adminLogin = curl.exe -s -X POST http://localhost:8000/auth/login -H "Content-Type: application/x-www-form-urlencoded" -d "username=admin@jsp.com&password=123456" | ConvertFrom-Json
$TOKEN_ADMIN = $adminLogin.access_token
Write-Host "✅ Admin logado" -ForegroundColor Green

$userLogin = curl.exe -s -X POST http://localhost:8000/auth/login -H "Content-Type: application/x-www-form-urlencoded" -d "username=user@jsp.com&password=123456" | ConvertFrom-Json
$TOKEN_USER = $userLogin.access_token
Write-Host "✅ User logado" -ForegroundColor Green

$tecLogin = curl.exe -s -X POST http://localhost:8000/auth/login -H "Content-Type: application/x-www-form-urlencoded" -d "username=tec1@jsp.com&password=123456" | ConvertFrom-Json
$TOKEN_TEC = $tecLogin.access_token
Write-Host "✅ Técnico logado" -ForegroundColor Green

Write-Host ""
Write-Host "TESTE 3: /auth/users User -> 403" -ForegroundColor Yellow
Write-Host "=================================" -ForegroundColor Yellow

$resp = curl.exe -s -w "`nHTTP:%{http_code}" -X GET http://localhost:8000/auth/users -H "Authorization: Bearer $TOKEN_USER"
if ($resp -match "HTTP:403") {
    Write-Host "✅ TESTE 3 PASSOU - User bloqueado (403)" -ForegroundColor Green
} else {
    Write-Host "❌ TESTE 3 FALHOU" -ForegroundColor Red
    Write-Host $resp
}

Write-Host ""
Write-Host "TESTE 4: Order Outro User -> 404" -ForegroundColor Yellow
Write-Host "================================" -ForegroundColor Yellow

$order = curl.exe -s -X POST http://localhost:8000/orders -H "Authorization: Bearer $TOKEN_USER" -H "Content-Type: application/json" -d '{"description":"Teste","total":50.00}' | ConvertFrom-Json
$ORDER_ID = $order.id
Write-Host "📦 Pedido criado: $ORDER_ID"

$resp = curl.exe -s -w "`nHTTP:%{http_code}" -X GET "http://localhost:8000/orders/$ORDER_ID" -H "Authorization: Bearer $TOKEN_TEC"
if ($resp -match "HTTP:404") {
    Write-Host "✅ TESTE 4 PASSOU - Técnico bloqueado (404)" -ForegroundColor Green
} else {
    Write-Host "❌ TESTE 4 FALHOU" -ForegroundColor Red
    Write-Host $resp
}

Write-Host ""
Write-Host "TESTE 5: Rate Limit -> 429" -ForegroundColor Yellow
Write-Host "==========================" -ForegroundColor Yellow

$rate_limit_ok = $false
for ($i=1; $i -le 6; $i++) {
    $resp = curl.exe -s -w "`nHTTP:%{http_code}" -X POST http://localhost:8000/auth/login -H "Content-Type: application/x-www-form-urlencoded" -d "username=admin@jsp.com&password=ERRADO"
    
    if ($resp -match "HTTP:429") {
        Write-Host "✅ TESTE 5 PASSOU - Rate limit ativado na tentativa $i (429)" -ForegroundColor Green
        $rate_limit_ok = $true
        break
    }
    
    Start-Sleep -Milliseconds 200
}

if (-not $rate_limit_ok) {
    Write-Host "❌ TESTE 5 FALHOU - Não atingiu rate limit" -ForegroundColor Red
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  ✅ VALIDAÇÃO CONCLUÍDA" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
