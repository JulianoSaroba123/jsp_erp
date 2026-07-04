# 🚀 Guia Rápido - Sistema JSP ERP (Modo Aplicativo)

## 🎯 Como Usar o Sistema

O JSP ERP foi configurado para funcionar como um **aplicativo desktop**! 
Basta clicar e o sistema abre automaticamente no navegador.

### ⭐ Modo Mais Fácil: Atalho na Área de Trabalho

1. **Clique no ícone "JSP ERP"** na sua área de trabalho
2. Aguarde alguns segundos (o sistema está iniciando em background)
3. **O navegador abrirá automaticamente** com o sistema pronto!

### 📁 Modo Alternativo: Pasta do Projeto

Se preferir iniciar pela pasta do projeto:

1. Dê **duplo clique** no arquivo `INICIAR_SISTEMA.bat`
2. O sistema irá:
   - ✅ Verificar e iniciar o Docker Desktop
   - ✅ Iniciar o banco de dados PostgreSQL (em background)
   - ✅ Iniciar o backend FastAPI (janela minimizada)
   - ✅ Iniciar o frontend React (janela minimizada)
   - ✅ **Abrir automaticamente no navegador**

## 🛑 Como Parar o Sistema

### Opção 1: Duplo Clique
Dê **duplo clique** no arquivo `PARAR_SISTEMA.bat`

### Opção 2: Via PowerShell
```powershell
.\PARAR_SISTEMA.ps1
```

> ⚠️ **Importante**: Feche o navegador, mas **não feche as janelas minimizadas do PowerShell** manualmente. Use o script de parada para encerrar tudo corretamente.

## 🌐 URLs do Sistema

Após iniciar, o sistema estará disponível em:

| Serviço | URL | Abre Automaticamente |
|---------|-----|---------------------|
| 🌐 Frontend | http://localhost:5173 | ✅ Sim |
| 🔌 Backend API | http://localhost:8000 | Opcional |
| 📚 Documentação | http://localhost:8000/docs | Se frontend não existir |
| 🗄️ Banco de Dados | localhost:5433 | Não |

## Credenciais Padrão

**Admin:**
- Email: `admin@jsp.com`
- Senha: (verificar no banco de dados)

**Banco de Dados:**
- Usuário: `jsp_user`
- Senha: `jsp123456`
- Database: `jsp_erp`
- Porta: `5433`

## Solução de Problemas

### Docker Desktop não inicia automaticamente
1. Abra o Docker Desktop manualmente
2. Aguarde até aparecer "Docker Desktop is running"
3. Execute o script novamente

### Erro de porta já em uso
Verifique se algum serviço já está usando as portas:
- **5433** (PostgreSQL)
- **8000** (Backend)
- **5173** (Frontend)

```powershell
# Verificar portas em uso
netstat -ano | findstr "5433"
netstat -ano | findstr "8000"
netstat -ano | findstr "5173"
```

### Backend não conecta ao banco
1. Verifique se o container está rodando: `docker ps`
2. Teste a conexão manualmente: `docker-compose logs db`

## Estrutura dos Arquivos

```
jsp-erp/
├── INICIAR_SISTEMA.bat     ← Duplo clique para INICIAR
├── INICIAR_SISTEMA.ps1     ← Script PowerShell de inicialização
├── PARAR_SISTEMA.bat       ← Duplo clique para PARAR
├── PARAR_SISTEMA.ps1       ← Script PowerShell de parada
└── docker-compose.yml      ← Configuração do banco de dados
```

## 💡 Como Funciona (Nos Bastidores)

O sistema roda em **modo background**:

1. 🐳 **Docker**: Banco de dados PostgreSQL em container
2. 🐍 **Backend**: FastAPI rodando em janela minimizada (porta 8000)
3. ⚛️ **Frontend**: React/Vite em janela minimizada (porta 5173)
4. 🌐 **Navegador**: Abre automaticamente na URL do frontend

As janelas ficam **minimizadas na barra de tarefas** para você ver os logs se necessário.

## 🔧 Criar Atalho na Área de Trabalho

Se o atalho não foi criado automaticamente:

1. Dê duplo clique em `CRIAR_ATALHO_DESKTOP.bat`
2. Um ícone "JSP ERP" aparecerá na sua área de trabalho

## 🔍 Ver Logs do Sistema

Se precisar debugar ou ver o que está acontecendo:

1. Clique nas **janelas minimizadas** do PowerShell na barra de tarefas
2. Você verá:
   - 🟢 **Janela 1**: Backend FastAPI (logs da API)
   - 🔵 **Janela 2**: Frontend React (logs do Vite)

## 📊 Status do Sistema

Para verificar se tudo está rodando:

```powershell
# Ver containers Docker
docker ps

# Ver processos Python (Backend)
Get-Process python

# Ver processos Node (Frontend)
Get-Process node
```

## 🎯 Arquivos do Sistema

```
jsp-erp/
├── 🚀 JSP ERP (atalho)         ← Atalho na área de trabalho
├── ▶️  INICIAR_SISTEMA.bat     ← Inicia o sistema (abre no navegador)
├── ⏹️  PARAR_SISTEMA.bat       ← Para o sistema completamente
├── 🔗 CRIAR_ATALHO_DESKTOP.bat ← Cria atalho na área de trabalho
└── 📖 COMO_USAR.md             ← Este guia
```

## ✨ Dicas e Boas Práticas

💡 **Primeira Execução**: O Docker pode demorar 1-2 minutos para baixar a imagem do PostgreSQL.

💡 **Desenvolvimento**: Deixe o sistema rodando enquanto trabalha. Ele detecta mudanças automaticamente (hot reload).

💡 **Fechar Navegador**: Pode fechar o navegador à vontade. O sistema continua rodando em background.

💡 **Performance**: Se o computador está lento, verifique se o Docker Desktop não está consumindo muita RAM.

💡 **Múltiplas Abas**: Pode abrir várias abas do sistema no navegador sem problemas.

## 🆘 Resolução de Problemas

### "O navegador não abriu automaticamente"
Abra manualmente: http://localhost:5173

### "Página não carrega"
1. Verifique se as janelas do PowerShell estão minimizadas (não fechadas)
2. Execute: `.\PARAR_SISTEMA.bat` e depois `.\INICIAR_SISTEMA.bat` novamente

### "Docker Desktop não inicia"
1. Abra o Docker Desktop manualmente
2. Aguarde até mostrar "Docker Desktop is running" (canto inferior esquerdo)
3. Execute o script novamente

### "Erro de porta já em uso"
Verifique se algum serviço já está usando as portas:
```powershell
netstat -ano | findstr "5433"  # PostgreSQL
netstat -ano | findstr "8000"  # Backend
netstat -ano | findstr "5173"  # Frontend
```

---

**✅ Sistema configurado em modo aplicativo!**  
Basta clicar no atalho da área de trabalho e começar a usar. 🚀
