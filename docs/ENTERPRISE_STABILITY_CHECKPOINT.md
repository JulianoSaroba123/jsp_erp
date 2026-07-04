# JSP ERP — ENTERPRISE STABILITY CHECKPOINT

Data do checkpoint: 2026-05-28

## Estado Atual
- Branch atual: feature/etapa-6-enterprise
- Commit atual: d9f06fd
- Coverage backend: 68.61%
- Total de testes backend: 383 passed
- Status das migrations (alembic current): 025_reconcile_legacy_column_names (head)
- Módulos homologados: Auth, Orders/Service Orders, Financial, Suppliers, Products, Proposals

## Arquitetura Validada
- FastAPI
- PostgreSQL
- SQLAlchemy
- Alembic
- Pytest
- JWT
- Multi-tenant
- CI/CD

## Módulos Estáveis
- Auth
- Orders/Service Orders
- Financial
- Suppliers
- Products
- Proposals

## Riscos Conhecidos
- Frontend enterprise ainda em evolução
- Coverage frontend não consolidado
- Staging ainda não homologado
- Build frontend com erros TypeScript no momento do checkpoint (14 erros em Customers, Products, ServiceOrders e Settings)

## Próxima Sprint Oficial
Frontend Enterprise OS

## Estratégia Segura de Branches
- master/main: estado estável homologado e releases
- develop: integração controlada de funcionalidades validadas
- feature/*: desenvolvimento isolado por módulo/escopo
- hotfix/*: correções emergenciais com fluxo curto e rastreável

## Validação Executada no Checkpoint
- pytest -q: OK (383 passed)
- alembic current: OK (head em 025_reconcile_legacy_column_names)
- frontend build: FALHOU (14 erros TypeScript; sem impacto no backend estável)
- backend startup: OK (FastAPI subiu e conectou no banco)

## Diretriz de Proteção do Estado Estável
- Não realizar commit gigante misturando backend estável e frontend experimental
- Não alterar migrations antigas já reconciliadas
- Não alterar regras de negócio sem branch isolada
- Não remover arquivos sem auditoria e classificação prévia
