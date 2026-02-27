# VALIDAÇÃO ALEMBIC - ETAPA 6

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  VALIDAÇÃO ALEMBIC - ETAPA 6" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# [1] Listar migrations
Write-Host "[1/4] Migrations encontradas:" -ForegroundColor Yellow
Get-ChildItem -Path "alembic\versions\*.py" | ForEach-Object {
    Write-Host "   - $($_.Name)" -ForegroundColor Gray
}

# [2] Histórico
Write-Host "`n[2/4] Histórico de migrations:" -ForegroundColor Yellow
alembic history --verbose

# [3] Heads
Write-Host "`n[3/4] Heads (versões finais):" -ForegroundColor Yellow
alembic heads

# [4] Verificar database e executar upgrade
Write-Host "`n[4/4] Testando database e upgrade..." -ForegroundColor Yellow

try {
    alembic current
    Write-Host "`nExecutando upgrade head..." -ForegroundColor Cyan
    alembic upgrade head
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "`nOK: Upgrade executado com sucesso" -ForegroundColor Green
        Write-Host "Versão atual no banco:" -ForegroundColor Cyan
        alembic current
    }
} catch {
    Write-Host "AVISO: Database não disponível" -ForegroundColor Yellow
}

Write-Host "`n========================================" -ForegroundColor Green
Write-Host "  VALIDAÇÃO CONCLUÍDA" -ForegroundColor Green
Write-Host "========================================`n" -ForegroundColor Green
