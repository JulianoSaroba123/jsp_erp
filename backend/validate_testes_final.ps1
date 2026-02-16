# VALIDACAO COMPLETA - TESTES 2-5
# Execução limpa sem debug logs

Write-Host ""
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "  VALIDACAO ETAPA 2 - TESTES 2-5" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# Health check
Write-Host "[PRE] Verificando API..." -ForegroundColor Gray
$health = curl.exe -s http://localhost:8000/health 2>$null | Select-String -Pattern '\{.*\}' | ForEach-Object { $_.Matches.Value } | ConvertFrom-Json
if ($health.app -eq "ERP JSP") {
    Write-Host "OK - API respondendo v$($health.version)" -ForegroundColor Green
} else {
    Write-Host "ERRO - API nao respondeu" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "TESTE 2: LOGIN -> TOKENS" -ForegroundColor Yellow
Write-Host "------------------------" -ForegroundColor Yellow

# Admin
$output = curl.exe -s -X POST http://localhost:8000/auth/login -H "Content-Type: application/x-www-form-urlencoded" -d "username=admin@jsp.com&password=123456" 2>$null
$json = $output | Select-String -Pattern '\{.*\}' | ForEach-Object { $_.Matches.Value }
$adminResp = $json | ConvertFrom-Json
$TOKEN_ADMIN = $adminResp.access_token
Write-Host "[OK] Admin logado - Token: $($TOKEN_ADMIN.Substring(0,20))..." -ForegroundColor Green

# User
$output = curl.exe -s -X POST http://localhost:8000/auth/login -H "Content-Type: application/x-www-form-urlencoded" -d "username=user@jsp.com&password=123456" 2>$null
$json = $output | Select-String -Pattern '\{.*\}' | ForEach-Object { $_.Matches.Value }
$userResp = $json | ConvertFrom-Json
$TOKEN_USER = $userResp.access_token
Write-Host "[OK] User logado - Token: $($TOKEN_USER.Substring(0,20))..." -ForegroundColor Green

# Tecnico
$output = curl.exe -s -X POST http://localhost:8000/auth/login -H "Content-Type: application/x-www-form-urlencoded" -d "username=tec1@jsp.com&password=123456" 2>$null
$json = $output | Select-String -Pattern '\{.*\}' | ForEach-Object { $_.Matches.Value }
$tecResp = $json | ConvertFrom-Json
$TOKEN_TEC = $tecResp.access_token
Write-Host "[OK] Tecnico logado - Token: $($TOKEN_TEC.Substring(0,20))..." -ForegroundColor Green

Write-Host ""
Write-Host "TESTE 3: /auth/users USER -> 403" -ForegroundColor Yellow
Write-Host "---------------------------------" -ForegroundColor Yellow

$output = curl.exe -s -w "`nHTTPSTATUS:%{http_code}" -X GET http://localhost:8000/auth/users -H "Authorization: Bearer $TOKEN_USER" 2>$null
$status = ($output | Select-String -Pattern "HTTPSTATUS:(\d+)").Matches.Groups[1].Value

if ($status -eq "403") {
    Write-Host "[OK] User bloqueado (403 Forbidden)" -ForegroundColor Green
} else {
    Write-Host "[FALHOU] Esperava 403, obteve $status" -ForegroundColor Red
}

# Controle: Admin deve conseguir
$output = curl.exe -s -w "`nHTTPSTATUS:%{http_code}" -X GET http://localhost:8000/auth/users -H "Authorization: Bearer $TOKEN_ADMIN" 2>$null
$status = ($output | Select-String -Pattern "HTTPSTATUS:(\d+)").Matches.Groups[1].Value

if ($status -eq "200") {
    Write-Host "[OK] Admin consegue listar (200 OK) - controle positivo" -ForegroundColor Green
} else {
    Write-Host "[ALERTA] Admin deveria conseguir (esperava 200, obteve $status)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "TESTE 4: ORDER OUTRO USER -> 404" -ForegroundColor Yellow
Write-Host "---------------------------------" -ForegroundColor Yellow

# User cria pedido (Decimal como float ou string no JSON)
$orderBody = '{"description":"Teste Multi-Tenant","total":99.90}'
$output = curl.exe -s -X POST http://localhost:8000/orders -H "Authorization: Bearer $TOKEN_USER" -H "Content-Type: application/json" -d $orderBody 2>$null
$json = $output | Select-String -Pattern '\{.*\}' | ForEach-Object { $_.Matches.Value }
$order = $json | ConvertFrom-Json
$ORDER_ID = $order.id

if ($ORDER_ID) {
    Write-Host "[OK] User criou pedido ID: $ORDER_ID" -ForegroundColor Green
} else {
    Write-Host "[ERRO] Falha ao criar pedido. Response:" -ForegroundColor Red
    Write-Host $json -ForegroundColor Red
    Write-Host "Tentando criar novamente com total como string..." -ForegroundColor Yellow
    $orderBody2 = '{"description":"Teste MT Fix","total":"99.90"}'
    $output2 = curl.exe -s -X POST http://localhost:8000/orders -H "Authorization: Bearer $TOKEN_USER" -H "Content-Type: application/json" -d $orderBody2 2>$null
    $json2 = $output2 | Select-String -Pattern '\{.*\}' | ForEach-Object { $_.Matches.Value }
    $order2 = $json2 | ConvertFrom-Json
    $ORDER_ID = $order2.id
    if ($ORDER_ID) {
        Write-Host "[OK] User criou pedido ID: $ORDER_ID (com total string)" -ForegroundColor Green
    } else {
        Write-Host "[ERRO CRITICO] Nao foi possivel criar pedido" -ForegroundColor Red
        Write-Host $json2 -ForegroundColor Red
        exit 1
    }
}

# User acessa seu proprio pedido (deve funcionar)
$output = curl.exe -s -w "`nHTTPSTATUS:%{http_code}" -X GET "http://localhost:8000/orders/$ORDER_ID" -H "Authorization: Bearer $TOKEN_USER" 2>$null
$status = ($output | Select-String -Pattern "HTTPSTATUS:(\d+)").Matches.Groups[1].Value

if ($status -eq "200") {
    Write-Host "[OK] User vê próprio pedido (200 OK)" -ForegroundColor Green
} else {
    Write-Host "[ALERTA] User deveria ver próprio pedido (obteve $status)" -ForegroundColor Yellow
}

# Técnico tenta acessar pedido do User (deve retornar 404)
$output = curl.exe -s -w "`nHTTPSTATUS:%{http_code}" -X GET "http://localhost:8000/orders/$ORDER_ID" -H "Authorization: Bearer $TOKEN_TEC" 2>$null
$status = ($output | Select-String -Pattern "HTTPSTATUS:(\d+)").Matches.Groups[1].Value

if ($status -eq "404") {
    Write-Host "[OK] Técnico bloqueado (404 Not Found) - anti-enumeration" -ForegroundColor Green
} else {
    Write-Host "[FALHOU] Esperava 404, obteve $status" -ForegroundColor Red
}

# Admin acessa qualquer pedido (deve funcionar)
$output = curl.exe -s -w "`nHTTPSTATUS:%{http_code}" -X GET "http://localhost:8000/orders/$ORDER_ID" -H "Authorization: Bearer $TOKEN_ADMIN" 2>$null
$status = ($output | Select-String -Pattern "HTTPSTATUS:(\d+)").Matches.Groups[1].Value

if ($status -eq "200") {
    Write-Host "[OK] Admin vê qualquer pedido (200 OK) - controle positivo" -ForegroundColor Green
} else {
    Write-Host "[ALERTA] Admin deveria ver qualquer pedido (obteve $status)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "TESTE 5: RATE LIMIT -> 429" -ForegroundColor Yellow
Write-Host "---------------------------" -ForegroundColor Yellow

$rate_limit_atingido = $false

for ($i=1; $i -le 6; $i++) {
    $output = curl.exe -s -w "`nHTTPSTATUS:%{http_code}" -X POST http://localhost:8000/auth/login -H "Content-Type: application/x-www-form-urlencoded" -d "username=admin@jsp.com&password=ERRADO" 2>$null
    $status = ($output | Select-String -Pattern "HTTPSTATUS:(\d+)").Matches.Groups[1].Value
    
    if ($status -eq "429") {
        Write-Host "[OK] Rate limit atingido na tentativa $i (429 Too Many Requests)" -ForegroundColor Green
        $rate_limit_atingido = $true
        break
    } else {
        Write-Host "[$i/6] Tentativa $i - Status: $status (esperado 401 até tentativa 5)" -ForegroundColor Gray
    }
    
    Start-Sleep -Milliseconds 500
}

if (-not $rate_limit_atingido) {
    Write-Host "[FALHOU] Não atingiu rate limit em 6 tentativas" -ForegroundColor Red
}

Write-Host ""
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "  VALIDACAO CONCLUIDA" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""
