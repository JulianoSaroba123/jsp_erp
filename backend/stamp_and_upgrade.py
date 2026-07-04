"""
Script para marcar migration 011 como aplicada manualmente (stamp)
"""
import subprocess
import sys

# Usar o comando stamp do Alembic para marcar a versão correta
result = subprocess.run(
    ['alembic', 'stamp', '010_create_suppliers'],
    capture_output=True,
    text=True
)

print(result.stdout)
if result.stderr:
    print("STDERR:", result.stderr, file=sys.stderr)

if result.returncode == 0:
    print("✅ Versão marcada como: 010_create_suppliers")
    print("   Agora rodando: alembic upgrade head")
    
    # Agora aplicar a 011
    result2 = subprocess.run(
        ['alembic', 'upgrade', 'head'],
        capture_output=True,
        text=True
    )
    
    print(result2.stdout)
    if result2.stderr:
        print("STDERR:", result2.stderr, file=sys.stderr)
    
    if result2.returncode == 0:
        print("✅ Migration 011 aplicada com sucesso!")
    else:
        print("❌ Erro ao aplicar migration 011")
        sys.exit(1)
else:
    print("❌ Erro ao marcar versão")
    sys.exit(1)
