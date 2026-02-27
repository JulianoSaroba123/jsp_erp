"""Limpar todas as tabelas RBAC"""
from app.database import engine
from sqlalchemy import text

print("Limpando tabelas RBAC...")

with engine.begin() as conn:
    conn.execute(text("TRUNCATE TABLE core.role_permissions CASCADE"))
    conn.execute(text("TRUNCATE TABLE core.user_roles CASCADE"))
    conn.execute(text("TRUNCATE TABLE core.permissions CASCADE"))
    conn.execute(text("TRUNCATE TABLE core.roles CASCADE"))
    conn.execute(text("TRUNCATE TABLE core.users CASCADE"))

print("✓ Tabelas limpas com sucesso!")
