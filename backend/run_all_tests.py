import subprocess
import sys

# Run pytest and save output
result = subprocess.run(
    [sys.executable, "-m", "pytest", "--tb=no", "-v"],
    capture_output=True,
    text=True,
    cwd=r"C:\Users\julia\Desktop\ERP_JSP Training\jsp-erp\backend"
)

# Save to file
with open("test_results.txt", "w", encoding="utf-8") as f:
    f.write(result.stdout)
    f.write("\n\n=== STDERR ===\n")
    f.write(result.stderr)

# Print summary
lines = result.stdout.split('\n')
for line in lines[-30:]:
    print(line)

print(f"\nExit code: {result.returncode}")
print("Full output saved to test_results.txt")
