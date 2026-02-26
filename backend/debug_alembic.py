"""
Diagnóstico profundo do Alembic - debug mode
"""
import sys
import os
from pathlib import Path

print("="*60)
print("DIAGNÓSTICO ALEMBIC - DEBUG MODE")
print("="*60)

# 1. Verificar paths
print("\n[1] VERIFICAÇÃO DE PATHS:")
print(f"   CWD: {os.getcwd()}")
print(f"   Python: {sys.version}")
print(f"   Encoding: {sys.getdefaultencoding()}")

# 2. Verificar arquivos de migration
print("\n[2] ARQUIVOS DE MIGRATION:")
versions_dir = Path("alembic/versions")
if versions_dir.exists():
    py_files = list(versions_dir.glob("*.py"))
    print(f"   Encontrados: {len(py_files)} arquivos")
    for f in sorted(py_files):
        print(f"   - {f.name}")
else:
    print(f"   ERRO: Diretório não existe: {versions_dir}")
    sys.exit(1)

# 3. Testar imports individuais
print("\n[3] TESTE DE IMPORTS:")
sys.path.insert(0, str(Path("alembic/versions").absolute()))

for py_file in sorted(py_files):
    try:
        with open(py_file, encoding='utf-8') as f:
            code = compile(f.read(), py_file.name, 'exec')
            namespace = {}
            exec(code, namespace)
            
            revision = namespace.get('revision', 'N/A')
            down_revision = namespace.get('down_revision', 'N/A')
            print(f"   ✓ {py_file.name}: {revision} <- {down_revision}")
    except Exception as e:
        print(f"   ✗ {py_file.name}: {e}")

# 4. Testar Alembic Config
print("\n[4] ALEMBIC CONFIG:")
try:
    from alembic.config import Config
    cfg = Config('alembic.ini')
    
    script_location = cfg.get_main_option('script_location')
    version_locations = cfg.get_main_option('version_locations')
    
    print(f"   script_location: {script_location}")
    print(f"   version_locations: {version_locations}")
    
    # Verificar se o diretório existe
    versions_path = Path(version_locations)
    print(f"   Path exists: {versions_path.exists()}")
    if versions_path.exists():
        files_count = len(list(versions_path.glob("*.py")))
        print(f"   Files in path: {files_count}")
    
except Exception as e

:
    print(f"   ERRO: {e}")
    import traceback
    traceback.print_exc()

# 5. Testar ScriptDirectory
print("\n[5] SCRIPT DIRECTORY:")
try:
    from alembic.script import ScriptDirectory
    script = ScriptDirectory.from_config(cfg)
    
    print(f"   Dir: {script.dir}")
    print(f"   Versions: {script.versions}")
    
    # Tentar iterar revisions
    try:
        revisions = list(script.walk_revisions())
        print(f"   Total revisions loaded: {len(revisions)}")
        
        for rev in revisions:
            print(f"   - {rev.revision} <- {rev.down_revision}")
    except Exception as e:
        print(f"   ERRO ao iterar revisions: {e}")
        import traceback
        traceback.print_exc()
    
    # Testar get_revisions
    try:
        all_revs = script.get_revisions('base:heads')
        print(f"   get_revisions(base:heads): {len(list(all_revs))}")
    except Exception as e:
        print(f"   ERRO em get_revisions: {e}")
        
except Exception as e:
    print(f"   ERRO: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)
print("FIM DO DIAGNÓSTICO")
print("="*60)
