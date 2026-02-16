#!/bin/bash
# =====================================
# Script de Migração Alembic (Bash)
# ETAPA 3B - Database Migrations
# =====================================
#
# Uso:
#   ./scripts/migrate.sh upgrade       # Aplica todas migrations pendentes
#   ./scripts/migrate.sh downgrade -1  # Reverte última migration
#   ./scripts/migrate.sh current       # Mostra versão atual
#   ./scripts/migrate.sh history       # Histórico de migrations
#   ./scripts/migrate.sh stamp head    # Marca como aplicada (banco existente)
#
# =====================================

set -e

# Cores para output
INFO='\033[0;36m'
SUCCESS='\033[0;32m'
ERROR='\033[0;31m'
WARNING='\033[0;33m'
NC='\033[0m' # No Color

function info() { echo -e "${INFO}ℹ️  $1${NC}"; }
function success() { echo -e "${SUCCESS}✅ $1${NC}"; }
function error() { echo -e "${ERROR}❌ $1${NC}"; }
function warning() { echo -e "${WARNING}⚠️  $1${NC}"; }

# =====================================
# Validar ambiente
# =====================================
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BACKEND_DIR="$SCRIPT_DIR/../backend"
ALEMBIC_INI="$BACKEND_DIR/alembic.ini"
ENV_FILE="$BACKEND_DIR/.env"

if [ ! -f "$ALEMBIC_INI" ]; then
    error "alembic.ini não encontrado em: $ALEMBIC_INI"
    exit 1
fi

if [ ! -f "$ENV_FILE" ]; then
    error "Arquivo .env não encontrado em: $ENV_FILE"
    info "Crie o arquivo .env com DATABASE_URL configurado"
    exit 1
fi

# =====================================
# Ativar venv (se existir)
# =====================================
VENV_ACTIVATE="$BACKEND_DIR/.venv/bin/activate"
if [ -f "$VENV_ACTIVATE" ]; then
    info "Ativando ambiente virtual..."
    source "$VENV_ACTIVATE"
else
    info "Ambiente virtual não encontrado, usando Python global"
fi

# =====================================
# Verificar Alembic instalado
# =====================================
if ! python -m alembic --version &> /dev/null; then
    error "Alembic não está instalado"
    info "Execute: pip install -r requirements.txt"
    exit 1
fi

# =====================================
# Processar comando
# =====================================
COMMAND="${1:-help}"
shift || true

cd "$BACKEND_DIR"

info "Executando: alembic $COMMAND $@"
echo ""

case "$COMMAND" in
    upgrade)
        TARGET="${1:-head}"
        python -m alembic upgrade "$TARGET"
        if [ $? -eq 0 ]; then
            success "Migration aplicada com sucesso!"
        else
            error "Falha ao aplicar migration"
            exit 1
        fi
        ;;
    
    downgrade)
        TARGET="${1:--1}"
        warning "ATENÇÃO: Downgrade pode remover dados!"
        read -p "Confirma downgrade para '$TARGET'? (s/N) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Ss]$ ]]; then
            python -m alembic downgrade "$TARGET"
            if [ $? -eq 0 ]; then
                success "Downgrade executado com sucesso"
            else
                error "Falha no downgrade"
                exit 1
            fi
        else
            info "Downgrade cancelado"
        fi
        ;;
    
    current)
        python -m alembic current
        if [ $? -ne 0 ]; then
            error "Falha ao obter versão atual"
            exit 1
        fi
        ;;
    
    history)
        python -m alembic history --verbose
        if [ $? -ne 0 ]; then
            error "Falha ao obter histórico"
            exit 1
        fi
        ;;
    
    stamp)
        TARGET="${1:-head}"
        info "Marcando database na versão: $TARGET"
        python -m alembic stamp "$TARGET"
        if [ $? -eq 0 ]; then
            success "Database marcado como versão: $TARGET"
        else
            error "Falha ao marcar versão"
            exit 1
        fi
        ;;
    
    revision)
        info "Criando nova migration..."
        python -m alembic revision --autogenerate "$@"
        if [ $? -eq 0 ]; then
            success "Migration criada! Revise o arquivo antes de aplicar."
        else
            error "Falha ao criar migration"
            exit 1
        fi
        ;;
    
    help|*)
        if [ "$COMMAND" != "help" ]; then
            error "Comando desconhecido: $COMMAND"
        fi
        echo ""
        echo "Comandos disponíveis:"
        echo "  upgrade [target]     - Aplica migrations (padrão: head)"
        echo "  downgrade [target]   - Reverte migrations (padrão: -1)"
        echo "  current              - Mostra versão atual"
        echo "  history              - Lista todas migrations"
        echo "  stamp [target]       - Marca versão sem executar (padrão: head)"
        echo "  revision [args]      - Cria nova migration"
        exit 1
        ;;
esac

echo ""
success "Operação concluída"
