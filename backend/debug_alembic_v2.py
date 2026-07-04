"""Diagnóstico profundo do Alembic"""
import sys
import os
from pathlib import Path

print("="*60)
print("DIAGNÓSTICO ALEMBIC")
print("="*60)

# 1. Paths
print("\n[1] PATHS:")
print(f"   CWD: {os.getcwd()}")
print(f"   Python: {sys.version.split()[0]}")

# 2. Arquivos
print("\n[2] ARQUIVOS:")
versions_dir = Path("alembic/versions")
py_files = list(versions_dir.glob("*.py"))
print(f"   Total: {len(py_files)}")
for f in sorted(py_files):
    print(f"   - {f.name}")

# 3. Imports
print("\n[3] TESTE DE IMPORTS:")
for py_file in sorted(py_files):
    try:
        with open(py_file, encoding='utf-8') as f:
            code = compile(f.read(), py_file.name, 'exec')
            namespace = {}
            exec(code, namespace)
            rev = namespace.get('revision', 'N/A')
            down = namespace.get('down_revision', 'N/A')
            print(f"   OK: {py_file.name}: {rev} <- {down}")
    except Exception as e:
        print(f"   ERRO: {py_file.name}: {e}")

# 4. Alembic Config
print("\n[4] ALEMBIC CONFIG:")
try:
    from alembic.config import Config
    cfg = Config('alembic.ini')
    script_loc = cfg.get_main_option('script_location')
    version_locs = cfg.get_main_option('version_locations')
    print(f"   script_location: {script_loc}")
    print(f"   version_locations: {version_locs}")
    print(f"   Path exists: {Path(version_locs).exists()}")
except Exception as e:
    print(f"   ERRO: {e}")

# 5. ScriptDirectory  
print("\n[5] SCRIPT DIRECTORY:")
try:
    from alembic.script import ScriptDirectory
    script = ScriptDirectory.from_config(cfg)
    print(f"   Dir: {script.dir}")
    print(f"   Versions dir: {script.versions}")
    
    revisions = list(script.walk_revisions())
    print(f"   Revisions loaded: {len(revisions)}")
    
    if len(revisions) == 0:
        print("\n   [DEBUG] Tentando carregar manualmente...")
        version_path = Path(script.versions)
        py_files = list(version_path.glob("*.py"))
        print(f"   Arquivos .py encontrados: {len(py_files)}")
        
        for pf in py_files:
            print(f"   Tentando: {pf.name}")
            try:
                mod_name = pf.stem
                script.get_revision(mod_name)
                print(f"      get_revision('{mod_name}'): OK")
            except Exception as e:
                print(f"      ERRO: {e}")
                
except Exception as e:
    print(f"   ERRO: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)
