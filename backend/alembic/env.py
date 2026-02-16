"""
Alembic Environment Configuration - ETAPA 3B
============================================

Este arquivo configura o ambiente de migrations do Alembic.

IMPORTANTE:
- Lê DATABASE_URL do arquivo .env (mesma fonte do app)
- Configura target_metadata dos models SQLAlchemy
- Trabalha com schema "core" (version_table_schema="core")
- Suporta migrações online (com conexão ativa) e offline (SQL)

"""
from logging.config import fileConfig
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# =====================================
# Carregar variáveis de ambiente
# =====================================
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL not set for Alembic")

# =====================================
# Configurar path para importar módulos do app
# =====================================
# Adicionar o diretório pai (backend/) ao Python path
backend_path = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_path))

# =====================================
# Importar models e configuração do app
# =====================================
from app.database import Base  # Base SQLAlchemy com todos os models

# Import explícito de todos os models para garantir registro no metadata
from app.models.user import User
from app.models.order import Order
from app.models.financial_entry import FinancialEntry

# =====================================
# Configuração do Alembic
# =====================================
config = context.config

# Sobrescrever sqlalchemy.url com o valor do .env
# CRÍTICO: Garante que migrations usem a mesma conexão do app
config.set_main_option("sqlalchemy.url", DATABASE_URL)

# Configurar logging (se alembic.ini tiver configuração de logging)
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Target metadata para autogenerate
# Este é o metadata agregado de todos os models SQLAlchemy
target_metadata = Base.metadata


# =====================================
# Funções auxiliares
# =====================================

def run_migrations_offline() -> None:
    """
    Migração OFFLINE: Gera SQL sem conectar ao banco.
    
    Útil para:
    - Gerar scripts SQL para revisão manual
    - Aplicar migrations em produção via script SQL
    - Debugging de migrations
    
    Uso:
        alembic upgrade head --sql > migration.sql
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        # Schema "core" para version table
        version_table_schema="core",
        # Incluir schema nas operações
        include_schemas=True,
        # Renderizar item imports (para autogenerate)
        render_as_batch=False,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Migração ONLINE: Conecta ao banco e executa migrations.
    
    Configuração:
    - Usa connection pooling (NullPool para evitar conexões persistentes)
    - Schema "core" para version_table
    - include_schemas=True para operações em schemas diferentes de public
    - compare_type=True para detectar mudanças de tipo de coluna
    """
    # Configuração do engine
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = DATABASE_URL
    
    # Criar engine com pooling adequado
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,  # Não manter pool (migrations são operações pontuais)
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            # Schema "core" para armazenar tabela alembic_version
            version_table_schema="core",
            # Incluir schemas nas operações DDL
            include_schemas=True,
            # Comparar tipos de colunas (para detectar alterações)
            compare_type=True,
            # Comparar server defaults
            compare_server_default=True,
            # Renderizar item imports
            render_as_batch=False,
        )

        with context.begin_transaction():
            context.run_migrations()


# =====================================
# Ponto de entrada
# =====================================
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
