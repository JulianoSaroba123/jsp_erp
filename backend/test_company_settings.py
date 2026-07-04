import os
import sys
sys.path.insert(0, ".")

# Simular o que acontece na função
values_string = os.getenv("COMPANY_VALUES", "Qualidade,Comprometimento,Inovação,Sustentabilidade,Ética")
print(f"valores_string tipo: {type(values_string)}")
print(f"valores_string: {values_string}")

values_list = [v.strip() for v in values_string.split(",")]
print(f"valores_list tipo: {type(values_list)}")
print(f"valores_list: {values_list}")

# Simular o template iterando
print("\nIterando sobre values:")
for value in values_list:
    print(f"  - {value}")
