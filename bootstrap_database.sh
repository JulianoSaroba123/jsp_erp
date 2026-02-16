#!/bin/bash
# ============================================================================
# BOOTSTRAP DO BANCO DE DADOS POSTGRESQL - ERP JSP
# Script para Linux/macOS (Bash)
# ============================================================================

set -e  # Exit on error

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
GRAY='\033[0;37m'
NC='\033[0m' # No Color

echo ""
echo -e "${CYAN}============================================${NC}"
echo -e "${CYAN}  BOOTSTRAP BANCO DE DADOS - PostgreSQL${NC}"
echo -e "${CYAN}============================================${NC}"
echo ""

# ============================================================================
# CONFIGURAÇÕES
# ============================================================================
DB_NAME="jsp_erp"
DB_USER="jsp_user"
DB_PASSWORD="jsp123456"
DB_HOST="localhost"
DB_PORT="5432"
CONTAINER_NAME="jsp_erp_db"
CONTAINER_IMAGE="postgres"

# ============================================================================
# PASSO 1: Verificar Docker
# ============================================================================
echo -e "${YELLOW}[1/7] Verificando Docker...${NC}"

if ! command -v docker &> /dev/null; then
    echo -e "${RED}  ERRO - Docker nao encontrado. Instale Docker.${NC}"
    exit 1
fi
echo -e "${GREEN}  OK - Docker instalado${NC}"

if ! docker ps &> /dev/null; then
    echo -e "${RED}  ERRO - Docker daemon nao esta rodando.${NC}"
    exit 1
fi
echo -e "${GREEN}  OK - Docker daemon rodando${NC}"

# ============================================================================
# PASSO 2: Descobrir e verificar container PostgreSQL
# ============================================================================
echo ""
echo -e "${YELLOW}[2/7] Descobrindo container PostgreSQL...${NC}"

# Tenta encontrar por nome, depois por imagem
CONTAINER_FOUND=$(docker ps --filter "name=$CONTAINER_NAME" --format "{{.Names}}" 2>/dev/null || true)

if [ -z "$CONTAINER_FOUND" ]; then
    echo -e "${GRAY}  Container '$CONTAINER_NAME' nao encontrado pelo nome${NC}"
    echo -e "${GRAY}  Tentando encontrar por imagem postgres...${NC}"
    
    CONTAINER_FOUND=$(docker ps --filter "ancestor=$CONTAINER_IMAGE" --format "{{.Names}}" | head -n 1 || true)
    
    if [ -n "$CONTAINER_FOUND" ]; then
        CONTAINER_NAME="$CONTAINER_FOUND"
        echo -e "${GREEN}  Container Postgres encontrado: $CONTAINER_NAME${NC}"
    else
        echo -e "${YELLOW}  AVISO - Nenhum container Postgres rodando${NC}"
        echo -e "${YELLOW}  Tentando iniciar via docker-compose...${NC}"
        
        docker-compose up -d db
        sleep 5
        
        CONTAINER_FOUND=$(docker ps --filter "name=jsp_erp_db" --format "{{.Names}}" 2>/dev/null || true)
        if [ -n "$CONTAINER_FOUND" ]; then
            CONTAINER_NAME="$CONTAINER_FOUND"
            echo -e "${GREEN}  OK - Container iniciado: $CONTAINER_NAME${NC}"
        else
            echo -e "${RED}  ERRO - Nao foi possivel iniciar container Postgres${NC}"
            exit 1
        fi
    fi
else
    echo -e "${GREEN}  OK - Container encontrado: $CONTAINER_NAME${NC}"
fi

# Verificar status
CONTAINER_STATUS=$(docker ps --filter "name=$CONTAINER_NAME" --format "{{.Status}}")
echo -e "${GRAY}  Status: $CONTAINER_STATUS${NC}"

# ============================================================================
# PASSO 3: Aguardar Postgres ficar pronto
# ============================================================================
echo ""
echo -e "${YELLOW}[3/7] Aguardando PostgreSQL aceitar conexoes...${NC}"

MAX_ATTEMPTS=30
ATTEMPT=0
READY=false

while [ $ATTEMPT -lt $MAX_ATTEMPTS ] && [ "$READY" = false ]; do
    ATTEMPT=$((ATTEMPT + 1))
    
    if docker exec "$CONTAINER_NAME" pg_isready -U "$DB_USER" -d "$DB_NAME" &> /dev/null; then
        READY=true
        echo -e "${GREEN}  OK - PostgreSQL pronto! ($ATTEMPT tentativas)${NC}"
    else
        echo -e "${GRAY}  Aguardando... $ATTEMPT/$MAX_ATTEMPTS${NC}"
        sleep 1
    fi
done

if [ "$READY" = false ]; then
    echo -e "${RED}  ERRO - PostgreSQL nao ficou pronto em ${MAX_ATTEMPTS}s${NC}"
    echo -e "${YELLOW}  Verifique os logs: docker logs $CONTAINER_NAME${NC}"
    exit 1
fi

# ============================================================================
# PASSO 4: Validar conectividade e contexto PRE-execução
# ============================================================================
echo ""
echo -e "${YELLOW}[4/7] Validando conectividade (via localhost:5432)...${NC}"

# Testar conexão via localhost (mesma que FastAPI usa)
export PGPASSWORD="$DB_PASSWORD"

if ! command -v psql &> /dev/null; then
    echo -e "${RED}  ERRO - psql nao encontrado. Instale PostgreSQL client tools.${NC}"
    exit 1
fi

CURRENT_DB=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT current_database();" 2>&1 | xargs)

if [ $? -eq 0 ]; then
    echo -e "${GREEN}  OK - Conectado em: $CURRENT_DB${NC}"
    
    if [ "$CURRENT_DB" != "$DB_NAME" ]; then
        echo -e "${YELLOW}  AVISO - Banco atual ($CURRENT_DB) diferente do esperado ($DB_NAME)${NC}"
    fi
else
    echo -e "${RED}  ERRO - Nao foi possivel conectar via localhost:$DB_PORT${NC}"
    echo -e "${YELLOW}  Certifique-se que porta 5432 esta acessivel${NC}"
    exit 1
fi

# Verificar versão
SERVER_VERSION=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT version();" 2>&1 | head -n 1 | xargs)
echo -e "${GRAY}  Versao: $SERVER_VERSION${NC}"

# Listar schemas ANTES da execução
echo ""
echo -e "${CYAN}  Schemas existentes ANTES:${NC}"
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "\dn"

# ============================================================================
# PASSO 5: Executar scripts SQL
# ============================================================================
# PASSO 5: Executar scripts SQL
# ============================================================================
echo ""
echo -e "${YELLOW}[5/7] Executando scripts SQL...${NC}"

# Script 1: Estrutura (schema core, tabela users)
echo ""
echo -e "${CYAN}  Executando: database/01_structure.sql${NC}"
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" < database/01_structure.sql > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo -e "${GREEN}  OK - 01_structure.sql executado${NC}"
else
    echo -e "${RED}  ERRO ao executar 01_structure.sql${NC}"
    exit 1
fi

# Script 2: Seed users (usuários iniciais)
echo ""
echo -e "${CYAN}  Executando: database/02_seed_users.sql${NC}"
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" < database/02_seed_users.sql > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo -e "${GREEN}  OK - 02_seed_users.sql executado${NC}"
else
    echo -e "${RED}  ERRO ao executar 02_seed_users.sql${NC}"
    exit 1
fi

# Script 3: Tabela orders
echo ""
echo -e "${CYAN}  Executando: database/03_orders.sql${NC}"
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" < database/03_orders.sql > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo -e "${GREEN}  OK - 03_orders.sql executado${NC}"
else
    echo -e "${RED}  ERRO ao executar 03_orders.sql${NC}"
    exit 1
fi

# Script 4: Tabela users (garantir estrutura idempotente)
echo ""
echo -e "${CYAN}  Executando: database/04_users.sql${NC}"
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" < database/04_users.sql > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo -e "${GREEN}  OK - 04_users.sql executado${NC}"
else
    echo -e "${RED}  ERRO ao executar 04_users.sql${NC}"
    exit 1
fi

# Script 5: Auth setup (índices e constraints adicionais)
echo ""
echo -e "${CYAN}  Executando: database/04_auth_setup.sql${NC}"
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" < database/04_auth_setup.sql > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo -e "${GREEN}  OK - 04_auth_setup.sql executado${NC}"
else
    echo -e "${RED}  ERRO ao executar 04_auth_setup.sql${NC}"
    exit 1
fi

# Script 6: Financial entries (ETAPA 3A)
echo ""
echo -e "${CYAN}  Executando: database/05_financial.sql${NC}"
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" < database/05_financial.sql > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo -e "${GREEN}  OK - 05_financial.sql executado (Lancamentos Financeiros)${NC}"
else
    echo -e "${RED}  ERRO ao executar 05_financial.sql${NC}"
    exit 1
fi

# ============================================================================
# PASSO 6: Validação completa POS-execução
# ============================================================================
echo ""
echo -e "${YELLOW}[6/7] Validando estrutura criada...${NC}"

# 6.1: Verificar schemas
echo ""
echo -e "${CYAN}  Verificando schema 'core'...${NC}"
SCHEMA_EXISTS=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM information_schema.schemata WHERE schema_name = 'core';" 2>&1 | xargs)

if [ "$SCHEMA_EXISTS" = "1" ]; then
    echo -e "${GREEN}  OK - Schema 'core' existe${NC}"
else
    echo -e "${RED}  ERRO - Schema 'core' NAO existe!${NC}"
    exit 1
fi

# 6.2: Verificar tabela users
echo ""
echo -e "${CYAN}  Verificando tabela 'core.users'...${NC}"
USERS_EXISTS=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT to_regclass('core.users');" 2>&1 | xargs)

if [ "$USERS_EXISTS" = "core.users" ]; then
    echo -e "${GREEN}  OK - Tabela 'core.users' existe${NC}"
    
    USER_COUNT=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM core.users;" 2>&1 | xargs)
    echo -e "${GRAY}  Total de usuarios: $USER_COUNT${NC}"
else
    echo -e "${RED}  ERRO - Tabela 'core.users' NAO existe!${NC}"
    exit 1
fi

# 6.3: Verificar tabela orders (SMOKE CHECK CRÍTICO)
echo ""
echo -e "${CYAN}  Verificando tabela 'core.orders' (SMOKE CHECK)...${NC}"
ORDERS_EXISTS=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT to_regclass('core.orders');" 2>&1 | xargs)

if [ "$ORDERS_EXISTS" = "core.orders" ]; then
    echo -e "${GREEN}  OK - Tabela 'core.orders' existe${NC}"
    
    ORDER_COUNT=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM core.orders;" 2>&1 | xargs)
    echo -e "${GRAY}  Total de pedidos: $ORDER_COUNT${NC}"
    
    # Mostrar estrutura
    echo ""
    echo -e "${CYAN}  Estrutura da tabela core.orders:${NC}"
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "\d core.orders"
else
    echo -e "${RED}  ERRO CRITICO - Tabela 'core.orders' NAO existe!${NC}"
    echo -e "${RED}  FastAPI vai falhar ao tentar acessar esta tabela.${NC}"
    exit 1
fi

# 6.4: Verificar via information_schema (validação alternativa)
echo ""
echo -e "${CYAN}  Validacao via information_schema...${NC}"
TABLE_CHECK=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'core' AND table_name = 'orders';" 2>&1 | xargs)

if [ "$TABLE_CHECK" = "1" ]; then
    echo -e "${GREEN}  OK - Tabela confirmada via information_schema${NC}"
else
    echo -e "${RED}  ERRO - Tabela NAO encontrada via information_schema${NC}"
    exit 1
fi

# ============================================================================
# PASSO 7: Resumo final
# ============================================================================
echo ""
echo -e "${YELLOW}[7/7] Resumo da configuracao...${NC}"
echo ""

SUMMARY=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "
SELECT 
    current_database() as database,
    current_user as \"user\",
    inet_server_addr() as server_addr,
    inet_server_port() as server_port;
" 2>&1)

echo -e "${CYAN}  Conexao validada:${NC}"
echo -e "${GRAY}  $SUMMARY${NC}"

# Limpar variável de senha
unset PGPASSWORD

# ============================================================================
# FINALIZAÇÃO
# ============================================================================
echo ""
echo -e "${CYAN}============================================${NC}"
echo -e "${GREEN}  BOOTSTRAP CONCLUIDO COM SUCESSO!${NC}"
echo -e "${CYAN}============================================${NC}"
echo ""

echo -e "${YELLOW}PROXIMOS PASSOS:${NC}"
echo ""
echo -e "${NC}1. Certifique-se que o FastAPI esta rodando:${NC}"
echo -e "${GRAY}   cd backend${NC}"
echo -e "${GRAY}   ./run.sh (ou use run.ps1 no Windows)${NC}"
echo ""
echo -e "${NC}2. Teste os endpoints:${NC}"
echo ""
echo -e "${GRAY}   # GET - Listar pedidos${NC}"
echo -e "${GRAY}   curl -s http://127.0.0.1:8000/orders | jq${NC}"
echo ""
echo -e "${GRAY}   # POST - Criar pedido (substitua USER_ID por UUID valido)${NC}"
echo -e "${GRAY}   curl -X POST http://127.0.0.1:8000/orders \\${NC}"
echo -e "${GRAY}        -H 'Content-Type: application/json' \\${NC}"
echo -e "${GRAY}        -d '{\"user_id\":\"UUID_AQUI\",\"description\":\"Teste\",\"total\":100.50}'${NC}"
echo ""
echo -e "${NC}3. Acesse a documentacao interativa:${NC}"
echo -e "${CYAN}   http://127.0.0.1:8000/docs${NC}"
echo ""
