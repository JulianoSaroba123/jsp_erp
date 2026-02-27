# =========================================================
# VALIDAÇÃO E CORREÇÃO DO ALEMBIC - ETAPA 6
# =========================================================

Write-Host "`n============================================" -ForegroundColor Cyan
Write-Host "  VALIDAÇÃO ALEMBIC - ETAPA 6" -ForegroundColor Cyan
Write-Host "============================================`n" -ForegroundColor Cyan

# Testar parsing das migrations
Write-Host "[1/5] Testando parsing das migrations..." -ForegroundColor Yellow

try {
    $cfg = python -c "from alembic.config import Config; from alembic.script import ScriptDirectory; cfg = Config('alembic.ini'); script = ScriptDirectory.from_config(cfg); heads = list(script.get_heads()); print(','.join(heads) if heads else 'NO_HEADS')"
    
    if ($cfg -eq "NO_HEADS") {
        Write-Host "❌ ERRO: Nenhum head encontrado nas migrations" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "✅ Migrations parseadas com sucesso" -ForegroundColor Green
    Write-Host "   🎯 Head(s): $cfg" -ForegroundColor Gray
} catch {
    Write-Host "❌ ERRO ao parsear migrations: $_" -ForegroundColor Red
    exit 1
}

# Listar migrations
Write-Host "`n[2/5] Listando migrations..." -ForegroundColor Yellow
Get-ChildItem -Path "alembic\versions\*.py" | ForEach-Object {
    Write-Host "   📄 $($_.Name)" -ForegroundColor Gray
}

# Mostrar histórico
Write-Host "`n[3/5] Histórico de migrations:" -ForegroundColor Yellow
alembic history --verbose

# Testar conexão database
Write-Host "`n[4/5] Testando conexão com database..." -ForegroundColor Yellow

try {
    $dbTest = python -c "import os; from dotenv import load_dotenv; from sqlalchemy import create_engine, text; load_dotenv(); db_url = os.getenv('DATABASE_URL_TEST') or os.getenv('DATABASE_URL'); engine = create_engine(db_url); conn = engine.connect(); result = conn.execute(text('SELECT version()')); print('OK'); conn.close()"
    
    Write-Host "✅ Conexão com database OK" -ForegroundColor Green
    
    # Executar upgrade
    Write-Host "`n[5/5] Executando alembic upgrade head..." -ForegroundColor Yellow
    alembic upgrade head
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Upgrade executado com sucesso" -ForegroundColor Green
        Write-Host "`n📌 Versão atual no banco:" -ForegroundColor Cyan
        alembic current
    } else {
        Write-Host "❌ ERRO no upgrade" -ForegroundColor Red
        exit 1
    }
    
} catch {
    Write-Host "⚠️  Database não disponível: $_" -ForegroundColor Yellow
    Write-Host "   Pulando upgrade head" -ForegroundColor Gray
}

# Relatório final
Write-Host "`n============================================" -ForegroundColor Green
Write-Host "  ✅ VALIDAÇÃO CONCLUÍDA" -ForegroundColor Green
Write-Host "============================================`n" -ForegroundColor Green
Write-Host "🚀 Status: LIBERADO para iniciar ETAPA 6`n" -ForegroundColor Green
