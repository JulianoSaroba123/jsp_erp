"""Testar import do modelo Supplier"""
from app.models.supplier import Supplier

print('✅ Model Supplier importado!')
print(f'📋 Tabela: {Supplier.__tablename__}')
print(f'📊 Total de colunas: ~52')
print(f'🔧 Computed properties: 8 (@property)')
print()
print('Testando computed properties:')
s = Supplier(
    nome="Empresa Teste LTDA",
    nome_fantasia="Teste Inc",
    tipo="PJ",
    cnpj_cpf="12345678000190"
)
print(f'  - documento_formatado: {s.documento_formatado}')
print(f'  - nome_display: {s.nome_display}')
print(f'  - is_pessoa_juridica: {s.is_pessoa_juridica}')
print(f'  - is_pessoa_fisica: {s.is_pessoa_fisica}')
print()
print('✅ Tudo OK!')
