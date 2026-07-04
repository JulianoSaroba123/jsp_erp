Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "MIGRATION 012: Proposals + Tipos de OS" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Ativar ambiente virtual
$venvPath = "c:\Users\julia\Desktop\ERP_JSP Training\jsp-erp\backend\.venv\Scripts\Activate.ps1"
if (Test-Path $venvPath) {
    Write-Host "✓ Ativando ambiente virtual..." -ForegroundColor Green
    & $venvPath
} else {
    Write-Host "✗ Ambiente virtual não encontrado em $venvPath" -ForegroundColor Red
    exit 1
}

# Navegar para diretório backend
Set-Location "c:\Users\julia\Desktop\ERP_JSP Training\jsp-erp\backend"

Write-Host ""
Write-Host "📋 Verificando versão atual do Alembic..." -ForegroundColor Yellow
python -c "from app.database import SessionLocal; from sqlalchemy import text; db = SessionLocal(); result = db.execute(text('SELECT version_num FROM alembic_version')); print('Versão atual:', result.scalar()); db.close()"

Write-Host ""
Write-Host "🚀 Aplicando migration 012..." -ForegroundColor Yellow
alembic upgrade head

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "=========================================" -ForegroundColor Green
    Write-Host "✅ MIGRATION 012 APLICADA COM SUCESSO!" -ForegroundColor Green
    Write-Host "=========================================" -ForegroundColor Green
    
    Write-Host ""
    Write-Host "📊 Verificando tabelas criadas..." -ForegroundColor Cyan
    
    # Verificar tabelas de proposals
    python -c "
from app.database import SessionLocal
from sqlalchemy import text
db = SessionLocal()
try:
    result = db.execute(text(\"\"\"
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'core' 
        AND table_name LIKE 'proposal%'
        ORDER BY table_name
    \"\"\"))
    print('Tabelas de Propostas:')
    for row in result:
        print(f'  ✓ {row[0]}')
except Exception as e:
    print(f'Erro: {e}')
finally:
    db.close()
"    
    Write-Host ""
    
    # Verificar novos campos em service_orders
    python -c "
from app.database import SessionLocal
from sqlalchemy import text
db = SessionLocal()
try:
    result = db.execute(text(\"\"\"
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns 
        WHERE table_schema = 'core' 
        AND table_name = 'service_orders'
        AND column_name IN ('tipo_ordem', 'exibir_valores', 'proposta_id', 'percentual_concluido', 'etapa_atual')
        ORDER BY column_name
    \"\"\"))
    print('Novos campos em service_orders:')
    for row in result:
        print(f'  ✓ {row[0]} ({row[1]}) - Nullable: {row[2]} - Default: {row[3]}')
except Exception as e:
    print(f'Erro: {e}')
finally:
    db.close()
"
    
    Write-Host ""
    Write-Host "📝 Próximos passos:" -ForegroundColor Cyan
    Write-Host "  1. Reiniciar o backend (Ctrl+C e rodar novamente)" -ForegroundColor White
    Write-Host "  2. Testar endpoint de Service Orders com novo campo tipo_ordem" -ForegroundColor White
    Write-Host "  3. Implementar rotas de Proposals" -ForegroundColor White
    Write-Host "  4. Testar conversão Proposta -> OS" -ForegroundColor White
    
} else {
    Write-Host ""
    Write-Host "=========================================" -ForegroundColor Red
    Write-Host "❌ ERRO AO APLICAR MIGRATION 012" -ForegroundColor Red
    Write-Host "=========================================" -ForegroundColor Red
    Write-Host "Verifique os logs acima para detalhes do erro." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Rollback (se necessário):" -ForegroundColor Cyan
    Write-Host "  alembic downgrade -1" -ForegroundColor White
}

Write-Host ""
Read-Host "Pressione Enter para continuar"
