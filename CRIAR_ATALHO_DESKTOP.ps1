# Script para criar atalho na área de trabalho

$desktopPath = [Environment]::GetFolderPath("Desktop")
$shortcutPath = "$desktopPath\JSP ERP.lnk"
$targetPath = "$PSScriptRoot\INICIAR_SISTEMA.bat"
$iconPath = "C:\Windows\System32\shell32.dll"

# Criar objeto WScript Shell
$shell = New-Object -ComObject WScript.Shell

# Criar atalho
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $targetPath
$shortcut.WorkingDirectory = "$PSScriptRoot"
$shortcut.Description = "Iniciar Sistema JSP ERP"
$shortcut.IconLocation = "$iconPath, 21"  # Ícone de aplicativo
$shortcut.Save()

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "Atalho criado com sucesso na area de trabalho!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Voce pode clicar no atalho 'JSP ERP' para iniciar o sistema!" -ForegroundColor Cyan
Write-Host ""

Start-Sleep -Seconds 3
