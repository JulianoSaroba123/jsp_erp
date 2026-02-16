#!/bin/bash
# ============================================
# SCRIPT DE SETUP DO BANCO DE DADOS POSTGRESQL
# Para Linux/macOS (Bash)
# ============================================

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
GRAY='\033[0;37m'
NC='\033[0m' # No Color

echo -e "${CYAN}"
echo "========================================"
echo "SETUP DO BANCO DE DADOS - PostgreSQL"
echo "========================================"
echo -e "${NC}"

# Variáveis do ambiente
DB_NAME="jsp_erp"
DB_USER="jsp_user"
DB_PASSWORD="jsp123456"
CONTAINER_NAME="jsp_erp_db"

# Passo 1: Verificar se Docker está rodando
echo -e "${YELLOW}[1/6] Verificando se Docker está rodando...${NC}"
if ! docker ps &> /dev/null; then
    echo -e "${RED}ERRO: Docker não está rodando! Inicie o Docker e tente novamente.${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Docker está rodando${NC}"

# Passo 2: Verificar se o container PostgreSQL existe e está rodando
echo -e "\n${YELLOW}[2/6] Verificando container PostgreSQL...${NC}"
CONTAINER_STATUS=$(docker ps --filter "name=$CONTAINER_NAME" --format "{{.Status}}" 2>/dev/null)

if [ -z "$CONTAINER_STATUS" ]; then
    echo -e "${YELLOW}Container '$CONTAINER_NAME' não encontrado. Tentando iniciar...${NC}"
    docker-compose up -d db
    sleep 5
    CONTAINER_STATUS=$(docker ps --filter "name=$CONTAINER_NAME" --format "{{.Status}}" 2>/dev/null)
    
    if [ -z "$CONTAINER_STATUS" ]; then
        echo -e "${RED}ERRO: Não foi possível iniciar o container. Execute 'docker-compose up -d' manualmente.${NC}"
        exit 1
    fi
fi

echo -e "${GREEN}✓ Container '$CONTAINER_NAME' está rodando: $CONTAINER_STATUS${NC}"

# Passo 3: Aguardar PostgreSQL estar pronto
echo -e "\n${YELLOW}[3/6] Aguardando PostgreSQL ficar pronto...${NC}"
MAX_ATTEMPTS=30
ATTEMPT=0
READY=false

while [ $ATTEMPT -lt $MAX_ATTEMPTS ] && [ "$READY" = false ]; do
    ATTEMPT=$((ATTEMPT + 1))
    if docker exec $CONTAINER_NAME pg_isready -U $DB_USER -d $DB_NAME &> /dev/null; then
        READY=true
        echo -e "${GREEN}✓ PostgreSQL está pronto!${NC}"
    else
        echo -e "${GRAY}  Tentativa $ATTEMPT/$MAX_ATTEMPTS... aguardando...${NC}"
        sleep 1
    fi
done

if [ "$READY" = false ]; then
    echo -e "${RED}ERRO: PostgreSQL não ficou pronto em tempo. Verifique os logs: docker logs $CONTAINER_NAME${NC}"
    exit 1
fi

# Passo 4: Executar script 01_structure.sql
echo -e "\n${YELLOW}[4/6] Executando 01_structure.sql (schema, users, seeds)...${NC}"
if docker exec -i $CONTAINER_NAME psql -U $DB_USER -d $DB_NAME < database/01_structure.sql; then
    echo -e "${GREEN}✓ Script 01_structure.sql executado com sucesso${NC}"
else
    echo -e "${RED}ERRO ao executar 01_structure.sql${NC}"
    exit 1
fi

# Passo 5: Executar script 03_orders.sql
echo -e "\n${YELLOW}[5/6] Executando 03_orders.sql (tabela orders)...${NC}"
if docker exec -i $CONTAINER_NAME psql -U $DB_USER -d $DB_NAME < database/03_orders.sql; then
    echo -e "${GREEN}✓ Script 03_orders.sql executado com sucesso${NC}"
else
    echo -e "${RED}ERRO ao executar 03_orders.sql${NC}"
    exit 1
fi

# Passo 6: Validar estrutura criada
echo -e "\n${YELLOW}[6/6] Validando estrutura do banco...${NC}"

echo -e "\n${CYAN}  → Verificando schema 'core'...${NC}"
docker exec $CONTAINER_NAME psql -U $DB_USER -d $DB_NAME -c "\dn core"

echo -e "\n${CYAN}  → Verificando tabela 'core.users'...${NC}"
CHECK_USERS=$(docker exec $CONTAINER_NAME psql -U $DB_USER -d $DB_NAME -t -c "SELECT to_regclass('core.users');")
echo -e "${GRAY}    Resultado: $CHECK_USERS${NC}"

echo -e "\n${CYAN}  → Verificando tabela 'core.orders'...${NC}"
CHECK_ORDERS=$(docker exec $CONTAINER_NAME psql -U $DB_USER -d $DB_NAME -t -c "SELECT to_regclass('core.orders');")
echo -e "${GRAY}    Resultado: $CHECK_ORDERS${NC}"

if [[ "$CHECK_ORDERS" == *"core.orders"* ]]; then
    echo -e "\n${GREEN}✓ Tabela 'core.orders' existe!${NC}"
else
    echo -e "\n${RED}AVISO: Tabela 'core.orders' não foi encontrada!${NC}"
fi

echo -e "\n${CYAN}  → Listando colunas de core.orders...${NC}"
docker exec $CONTAINER_NAME psql -U $DB_USER -d $DB_NAME -c "\d core.orders"

echo -e "\n${CYAN}  → Contando registros em core.users...${NC}"
docker exec $CONTAINER_NAME psql -U $DB_USER -d $DB_NAME -c "SELECT COUNT(*) as total_users FROM core.users;"

echo -e "\n${CYAN}  → Contando registros em core.orders...${NC}"
docker exec $CONTAINER_NAME psql -U $DB_USER -d $DB_NAME -c "SELECT COUNT(*) as total_orders FROM core.orders;"

# Finalização
echo -e "\n${CYAN}"
echo "========================================"
echo -e "${GREEN}SETUP CONCLUÍDO!${NC}"
echo -e "${CYAN}========================================${NC}"

echo -e "\n${YELLOW}📋 PRÓXIMOS PASSOS:${NC}"
echo -e "${NC}1. Certifique-se que o servidor FastAPI está rodando:${NC}"
echo -e "${GRAY}   cd backend && ./run.sh${NC}"
echo -e "\n${NC}2. Teste o endpoint GET /orders:${NC}"
echo -e "${GRAY}   curl -s http://127.0.0.1:8000/orders?page=1&page_size=20 | jq${NC}"
echo -e "\n${NC}3. Ou abra no navegador:${NC}"
echo -e "${GRAY}   http://127.0.0.1:8000/docs${NC}"
echo ""
