# JSP ERP

[![tests](https://github.com/JulianoSaroba123/jsp_erp/actions/workflows/tests.yml/badge.svg?branch=master)](https://github.com/JulianoSaroba123/jsp_erp/actions/workflows/tests.yml)

Sistema ERP desenvolvido com FastAPI e PostgreSQL.

## 📊 Status do Projeto

- ✅ **63/63 testes passando**
- ✅ **CI/CD automatizado** (GitHub Actions)
- ✅ **Coverage HTML** disponível nos artefatos
- 🎯 **Meta de Coverage:** 75% (atual: verificar artefato)

## 🚀 Tecnologias

- **Backend:** FastAPI + Python 3.11
- **Database:** PostgreSQL 15
- **ORM:** SQLAlchemy + Alembic
- **Autenticação:** JWT (python-jose + bcrypt)
- **Testes:** pytest + pytest-cov
- **CI/CD:** GitHub Actions

## 🧪 Executar Testes Localmente

```bash
cd backend
python -m pytest --cov=app --cov-report=term-missing --cov-report=html
```

Relatório HTML será gerado em `backend/htmlcov/index.html`

## 📦 Estrutura do Projeto

```
jsp-erp/
├── backend/
│   ├── app/
│   │   ├── auth/          # Autenticação e segurança
│   │   ├── models/        # Modelos SQLAlchemy
│   │   ├── repositories/  # Camada de acesso a dados
│   │   ├── routers/       # Endpoints FastAPI
│   │   ├── schemas/       # Pydantic schemas
│   │   ├── services/      # Lógica de negócio
│   │   └── utils/         # Utilitários
│   ├── tests/             # Testes automatizados
│   └── alembic/           # Migrations
├── database/              # Scripts SQL
└── .github/workflows/     # CI/CD
```

## 🔒 Branch Protection

Branch `master` protegida com:
- ✅ Pull Request obrigatório
- ✅ Status checks devem passar (CI)
- ✅ Branch deve estar atualizada antes do merge

## 📈 Roadmap de Coverage

### Sprint 1 (Meta: 70%)
- [ ] Services layer completo
- [ ] Auth endpoints críticos
- [ ] Order repository edge cases

### Sprint 2 (Meta: 75%)
- [ ] Middleware de logging
- [ ] Exception handlers
- [ ] Financial sync paths

### Sprint 3 (Meta: 80%)
- [ ] User management completo
- [ ] Soft delete scenarios
- [ ] Pagination utilities

## 📝 Licença

Projeto privado - JSP Training
