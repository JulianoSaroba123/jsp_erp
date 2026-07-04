Set-Location 'C:\Users\julia\Desktop\ERP_JSP Training\jsp-erp\backend'
if (Test-Path '.venv\Scripts\Activate.ps1') {
    .\.venv\Scripts\Activate.ps1
}
$host.ui.RawUI.WindowTitle = 'JSP ERP - Backend API (Porta 8000)'
Write-Host '============================================================' -ForegroundColor Green
Write-Host 'JSP ERP - BACKEND FASTAPI RODANDO' -ForegroundColor Green
Write-Host 'URL: http://localhost:8000' -ForegroundColor Cyan
Write-Host 'Docs: http://localhost:8000/docs' -ForegroundColor Cyan
Write-Host '============================================================' -ForegroundColor Green
Write-Host ''
Write-Host 'Mantenha esta janela aberta enquanto usa o sistema.' -ForegroundColor Yellow
Write-Host 'Para parar o backend, feche esta janela ou pressione Ctrl+C' -ForegroundColor Gray
Write-Host ''
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
