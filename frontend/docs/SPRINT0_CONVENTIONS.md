# Sprint 0 Front-end Enterprise - Convencoes

## Status
- Sprint 0 concluida e aprovada.
- Indice central da documentacao: [README.md](./README.md)

## Objetivo da Etapa 1
- Criar fundacao modular sem alterar regras de negocio
- Reorganizar providers e roteamento com baixo risco
- Preservar todas as rotas atuais

## Estrutura base criada
- src/app
- src/providers
- src/router
- src/layouts
- src/features
- src/design-system
- src/shared
- src/types
- src/utils
- src/styles

## Convencoes iniciais
- Providers globais ficam em src/providers
- Configuracao de rotas fica em src/router
- Composicao da aplicacao fica em src/app
- Layouts reutilizaveis ficam em src/layouts
- Features de negocio serao modularizadas em src/features nas proximas etapas

## Guardrails
- Sem mudancas no backend
- Sem mudancas em contratos de API
- Sem refatoracao de telas de negocio nesta etapa
- Sem dependencias novas nesta etapa

## Encerramento
- Etapa 1 concluida: fundacao modular e providers/router.
- Etapa 2 concluida: tokens, temas dark/light e base global de estilos.
- Etapa 3 concluida: componentes base minimos do design system.
- Etapa 4 concluida: consolidacao de auth, sessao, HTTP e RBAC visual.
- Etapa 5 concluida: DataTable Enterprise e Dashboard Foundation (placeholders).
