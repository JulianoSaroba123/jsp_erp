# Bootstrap do Banco de Dados PostgreSQL

Scripts automatizados para configurar o banco de dados do projeto ERP JSP.

## 📋 Requisitos

- Docker e Docker Compose instalados e rodando
- PostgreSQL client tools (`psql`) instalado
- Container PostgreSQL rodando (ou será iniciado automaticamente)

## 🚀 Uso Rápido

### Windows (PowerShell)

```powershell
cd "C:\Users\julia\Desktop\ERP_JSP Training\jsp-erp"
.\bootstrap_database.ps1
```

### Linux/macOS (Bash)

```bash
cd ~/jsp-erp
chmod +x bootstrap_database.sh
./bootstrap_database.sh
```

## 📝 O que o script faz

1. ✅ Verifica se Docker está rodando
2. ✅ Descobre automaticamente o container PostgreSQL
3. ✅ Aguarda o Postgres ficar pronto
4. ✅ Valida conectividade via `localhost:5432` (mesma conexão que FastAPI usa)
5. ✅ Executa scripts SQL:
   - `database/01_structure.sql` (schema core, tabela users, seeds)
   - `database/03_orders.sql` (tabela orders)
6. ✅ Valida estrutura criada (SMOKE CHECK):
   - Schema `core` existe
   - Tabela `core.users` existe
   - Tabela `core.orders` existe ⚠️ **CRÍTICO**
7. ✅ Exibe resumo da configuração

## ⚠️ SMOKE CHECK

O script **FALHA com exit code 1** se:
- Docker não estiver rodando
- Container PostgreSQL não for encontrado
- Postgres não aceitar conexões em 30s
- Não conseguir conectar via `localhost:5432`
- Scripts SQL falharem
- Schema `core` não existir após execução
- Tabela `core.orders` não existir após execução

**Isso garante que FastAPI nunca rodará sem o banco configurado corretamente!**

## 🧪 Após executar o bootstrap

### Teste 1: Verificar tabelas diretamente

```bash
# Windows PowerShell
$env:PGPASSWORD="jsp123456"
psql -h localhost -p 5432 -U jsp_user -d jsp_erp -c "\dt core.*"

# Linux/macOS
PGPASSWORD=jsp123456 psql -h localhost -p 5432 -U jsp_user -d jsp_erp -c "\dt core.*"
```

### Teste 2: Iniciar FastAPI

```bash
cd backend
.\run.ps1  # Windows
./run.sh   # Linux/macOS
```

### Teste 3: Testar endpoints

```bash
# GET - Listar pedidos
curl http://127.0.0.1:8000/orders

# POST - Criar pedido (substitua USER_ID)
curl -X POST http://127.0.0.1:8000/orders \
  -H "Content-Type: application/json" \
  -d '{"user_id":"UUID_AQUI","description":"Teste Bootstrap","total":99.99}'

# Acessar documentação interativa
# http://127.0.0.1:8000/docs
```

## 🐛 Troubleshooting

### Erro: "Docker não está rodando"

**Solução:** Inicie Docker Desktop e aguarde o ícone ficar verde.

### Erro: "psql não encontrado"

**Windows:**
```powershell
# Instale PostgreSQL client ou via choco
choco install postgresql
```

**Linux (Debian/Ubuntu):**
```bash
sudo apt-get install postgresql-client
```

**macOS:**
```bash
brew install postgresql
```

### Erro: "Nao foi possivel conectar via localhost:5432"

**Verifique:**
1. Container está rodando? `docker ps | grep postgres`
2. Porta está publicada? `docker ps` (deve mostrar `0.0.0.0:5432->5432/tcp`)
3. Firewall bloqueando? Teste: `telnet localhost 5432`

### Erro: "Tabela core.orders NAO existe"

**Diagnóstico:**
```bash
# Verificar em qual banco está
PGPASSWORD=jsp123456 psql -h localhost -p 5432 -U jsp_user -d jsp_erp -c "SELECT current_database();"

# Listar schemas
PGPASSWORD=jsp123456 psql -h localhost -p 5432 -U jsp_user -d jsp_erp -c "\dn"

# Procurar tabela
PGPASSWORD=jsp123456 psql -h localhost -p 5432 -U jsp_user -d jsp_erp -c "SELECT to_regclass('core.orders');"
```

**Solução:** Execute o bootstrap novamente. Scripts são idempotentes (podem rodar múltiplas vezes).

## 📚 Documentação Técnica

Para entender a fundo o problema de "docker exec vs localhost", leia:

📖 **[docs/DIAGNOSTICO_TECNICO_POSTGRESQL.md](docs/DIAGNOSTICO_TECNICO_POSTGRESQL.md)**

Tópicos:
- Como docker exec e psql -h localhost funcionam
- As 3 causas mais prováveis de discrepância
- Checklist de validação
- Boas práticas anti-confusão
- Comandos de emergência
- Diagrama de arquitetura

## 🔒 Segurança

⚠️ **NUNCA commite senhas em produção!**

Os scripts usam credenciais do `.env` que **já estão no `.gitignore`**.

Para produção:
- Use secrets do Docker/Kubernetes
- Considere AWS RDS, Azure Database, ou managed Postgres
- Configure SSL/TLS para conexões externas

## 📄 Licença

Este projeto é parte do sistema ERP JSP - Treinamento JSP.

---

**Última atualização:** 2026-02-13  
**Versão dos scripts:** 1.0.0  
**Status:** ✅ Testado e funcionando
