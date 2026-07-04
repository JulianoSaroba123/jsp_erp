from pathlib import Path
from jinja2 import Environment, FileSystemLoader
import os

# Simular get_company_settings
values_list = ["Qualidade", "Comprometimento", "Inovação", "Sustentabilidade", "Ética"]

company = {
    "company_name": "JSP Automação Industrial & Solar",
    "values": values_list  # Lista direta
}

# Configurar Jinja2
template_dir = Path("app/templates")
env = Environment(loader=FileSystemLoader(str(template_dir)))

# Template mínimo para testar
template_string = """
<html>
<body>
    <h1>{{ company.company_name }}</h1>
    
    <h2>Valores:</h2>
    <ul>
    {% for value in company.values %}
        <li>{{ value }}</li>
    {% endfor %}
    </ul>
</body>
</html>
"""

# Criar template from string
from jinja2 import Template
template = Template(template_string)

html = template.render(company=company)
print("HTML gerado:")
print(html)
print("\nSucesso!")
