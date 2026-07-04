import sys
import subprocess

# Run pytest and capture output
result = subprocess.run(
    [sys.executable, "-m", "pytest", 
     "tests/test_rbac.py::TestRBACEnforcement::test_user_has_permission_method",
     "-xvs", "--tb=short"],
    capture_output=True,
    text=True,
    cwd=r"C:\Users\julia\Desktop\ERP_JSP Training\jsp-erp\backend"
)

# Print last 80 lines
lines = result.stdout.split('\n')
print('\n'.join(lines[-80:]))

# Print stderr if any
if result.stderr:
    print("\n=== STDERR ===")
    print('\n'.join(result.stderr.split('\n')[-20:]))
