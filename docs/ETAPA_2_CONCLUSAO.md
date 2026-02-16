# ✅ ETAPA 2 - AUTENTICAÇÃO E PERMISSÕES

**Status**: ✅ IMPLEMENTADO  
**Data**: Concluído  
**Objetivo**: Sistema de autenticação JWT + Controle de permissões multi-tenant

---

## 📦 O QUE FOI IMPLEMENTADO

### 1. Banco de Dados

#### ✅ Arquivo criado: `database/04_users.sql`
- Tabela `core.users` com estrutura idempotente
- Constraints de validação de roles (admin, user, technician, finance)
- Índices otimizados para email, role e is_active
- Comentários explicativos

#### ✅ Scripts de Bootstrap atualizados
- `bootstrap_database.ps1` - Windows PowerShell
- `bootstrap_database.sh` - Linux/macOS
- Ambos executam `04_users.sql` na sequência correta

---

### 2. Módulo de Autenticação (`app/auth/`)

#### ✅ `app/auth/security.py`
Funções de segurança:
- `hash_password()` - Gera hash bcrypt
- `verify_password()` - Valida senha contra hash
- `create_access_token()` - Cria token JWT (HS256)
- `decode_token()` - Valida e decodifica JWT

#### ✅ `app/auth/models.py`
Modelo SQLAlchemy `User`:
- UUID como chave primária
- Campos: name, email, password_hash, role, is_active
- Relacionamento com `Order`

#### ✅ `app/auth/repository.py`
Repository pattern para User:
- `get_by_email()` - Busca por email
- `get_by_id()` - Busca por UUID
- `create()` - Cria usuário
- `get_all_active()` - Lista usuários ativos
- `update()` - Atualiza usuário

#### ✅ `app/auth/service.py`
Lógica de negócio:
- `register()` - Cadastra novo usuário com validações
- `authenticate()` - Valida credenciais e retorna user

#### ✅ `app/auth/router.py`
Endpoints REST:
- `POST /auth/register` - Cadastro de usuário
- `POST /auth/login` - Login (retorna JWT)
- `GET /auth/me` - Dados do usuário autenticado
- `GET /auth/users` - Lista usuários (debug)

Dependency:
- `get_current_user()` - Extrai usuário do token JWT

---

### 3. Proteção de Rotas (Multi-tenant)

#### ✅ `app/routers/order_routes.py`
Todas as rotas protegidas com `Depends(get_current_user)`:

**GET /orders** - Listar pedidos
- **admin**: vê todos os pedidos
- **user/technician/finance**: vê apenas seus próprios pedidos

**POST /orders** - Criar pedido
- `user_id` é obtido do token JWT (não pode ser enviado no body)
- Pedido é criado automaticamente para o usuário autenticado

**DELETE /orders/{id}** - Deletar pedido
- **admin**: pode deletar qualquer pedido
- **user/technician/finance**: só pode deletar seus próprios pedidos

---

### 4. Configuração

#### ✅ `backend/.env.example`
Template de variáveis de ambiente:
```env
DATABASE_URL=postgresql+psycopg://jsp_user:jsp123456@localhost:5432/jsp_erp
SECRET_KEY=your-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
DEBUG=True
```

#### ✅ `app/config.py`
Configuração centralizada:
- Lê variáveis do `.env`
- Define `SECRET_KEY`, `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`
- Configurações de paginação e app

---

### 5. Seed de Usuários

#### ✅ `backend/seed_users.py`
Script Python para criar usuários de desenvolvimento:
```bash
python backend/seed_users.py
```

**Usuários criados:**
```
admin@jsp.com  | Senha: 123456 | Role: admin
tec1@jsp.com   | Senha: 123456 | Role: technician
fin@jsp.com    | Senha: 123456 | Role: finance
user@jsp.com   | Senha: 123456 | Role: user
```

⚠️ **Importante**: Usa hash bcrypt do Python (compatível com `passlib`)

---

## 🚀 COMO USAR

### Passo 1: Configurar .env

```bash
cd backend
cp .env.example .env
```

Edite `backend/.env` e ajuste `SECRET_KEY`:
```env
SECRET_KEY=uma-chave-secreta-longa-e-aleatoria-aqui
```

**Gerar chave segura:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

---

### Passo 2: Bootstrap do Banco

**Windows PowerShell:**
```powershell
.\bootstrap_database.ps1
```

**Linux/macOS:**
```bash
chmod +x bootstrap_database.sh
./bootstrap_database.sh
```

Isso cria:
- Schema `core`
- Tabela `core.users`
- Tabela `core.orders`
- Constraints e índices

---

### Passo 3: Seed de Usuários

```bash
cd backend
python seed_users.py
```

Saída esperada:
```
🌱 Iniciando seed de usuários...

✅ admin@jsp.com - criado (role: admin)
✅ tec1@jsp.com - criado (role: technician)
✅ fin@jsp.com - criado (role: finance)
✅ user@jsp.com - criado (role: user)

📊 Resumo: 4 criados, 0 já existiam
```

---

### Passo 4: Instalar Dependências

```bash
cd backend
pip install -r requirements.txt
```

**Dependências de auth:**
- `python-jose[cryptography]` - JWT
- `passlib[bcrypt]` - Hash de senha
- `email-validator` - Validação de email
- `pydantic[email]` - Schemas com EmailStr

---

### Passo 5: Rodar a API

**Windows PowerShell:**
```powershell
cd backend
.\run.ps1
```

**Linux/macOS:**
```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API disponível em: http://localhost:8000  
Documentação Swagger: http://localhost:8000/docs

---

## 🧪 TESTANDO A AUTENTICAÇÃO

### 1. Registrar Novo Usuário

**Endpoint**: `POST /auth/register`

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "teste@jsp.com",
    "password": "senha123",
    "name": "Usuário Teste",
    "role": "user"
  }'
```

**Resposta:**
```json
{
  "id": "uuid-aqui",
  "email": "teste@jsp.com",
  "name": "Usuário Teste",
  "role": "user",
  "is_active": true
}
```

---

### 2. Fazer Login

**Endpoint**: `POST /auth/login`

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@jsp.com&password=123456"
```

**Resposta:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": "uuid-aqui",
    "email": "admin@jsp.com",
    "name": "Admin JSP",
    "role": "admin",
    "is_active": true
  }
}
```

⚠️ **Copie o `access_token`** para usar nas próximas requests!

---

### 3. Verificar Usuário Autenticado

**Endpoint**: `GET /auth/me`

```bash
curl -X GET http://localhost:8000/auth/me \
  -H "Authorization: Bearer SEU_TOKEN_AQUI"
```

**Resposta:**
```json
{
  "id": "uuid-aqui",
  "email": "admin@jsp.com",
  "name": "Admin JSP",
  "role": "admin",
  "is_active": true
}
```

---

### 4. Criar Pedido (Autenticado)

**Endpoint**: `POST /orders`

```bash
curl -X POST http://localhost:8000/orders \
  -H "Authorization: Bearer SEU_TOKEN_AQUI" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Pedido de teste",
    "total": 150.50
  }'
```

✅ O `user_id` é extraído automaticamente do token JWT!

---

### 5. Listar Pedidos (Multi-tenant)

**Endpoint**: `GET /orders`

**Como admin** (vê todos):
```bash
curl -X GET http://localhost:8000/orders \
  -H "Authorization: Bearer TOKEN_DO_ADMIN"
```

**Como user** (vê só os seus):
```bash
curl -X GET http://localhost:8000/orders \
  -H "Authorization: Bearer TOKEN_DO_USER"
```

---

### 6. Deletar Pedido (Multi-tenant)

**Endpoint**: `DELETE /orders/{id}`

**Como admin** (pode deletar qualquer pedido):
```bash
curl -X DELETE http://localhost:8000/orders/uuid-do-pedido \
  -H "Authorization: Bearer TOKEN_DO_ADMIN"
```

**Como user** (só pode deletar os seus):
```bash
curl -X DELETE http://localhost:8000/orders/uuid-do-pedido \
  -H "Authorization: Bearer TOKEN_DO_USER"
```

Se tentar deletar pedido de outro usuário:
```json
{
  "detail": "Você não tem permissão para deletar este pedido"
}
```

---

## 🔐 TESTANDO NO SWAGGER UI

Acesse: http://localhost:8000/docs

### 1. Fazer Login
1. Vá em `POST /auth/login`
2. Clique em "Try it out"
3. Preencha:
   - username: `admin@jsp.com`
   - password: `123456`
4. Execute
5. **Copie o `access_token`** da resposta

### 2. Autorizar Swagger
1. Clique no botão **🔓 Authorize** (topo da página)
2. Cole o token copiado (sem "Bearer ")
3. Clique em "Authorize"
4. Clique em "Close"

Agora todas as rotas protegidas funcionarão automaticamente! 🎉

### 3. Testar Rotas Protegidas
- `GET /auth/me` - Ver seus dados
- `POST /orders` - Criar pedido
- `GET /orders` - Listar pedidos (filtragem automática por role)
- `DELETE /orders/{id}` - Deletar pedido (permissão por role)

---

## 🏗️ ARQUITETURA

```
app/
├── auth/                    # Módulo de autenticação
│   ├── __init__.py         # Exporta router e get_current_user
│   ├── router.py           # Endpoints: /auth/register, /login, /me
│   ├── service.py          # Lógica: register(), authenticate()
│   ├── repository.py       # DAO: get_by_email(), create()
│   └── security.py         # Hash de senha, JWT
├── models/
│   ├── user.py             # Model User (SQLAlchemy)
│   └── order.py            # Model Order (FK para User)
├── routers/
│   ├── order_routes.py     # Rotas protegidas com multi-tenant
│   └── ...
├── config.py               # Configuração (SECRET_KEY, etc.)
└── main.py                 # FastAPI app + middlewares
```

---

## 🔒 SEGURANÇA

### ✅ Implementado
- ✅ Hash de senha com **bcrypt** (via passlib)
- ✅ JWT com **HS256** (chave simétrica)
- ✅ Tokens expiram em **60 minutos**
- ✅ Validação de email (Pydantic EmailStr)
- ✅ Senha mínima: **6 caracteres**
- ✅ Roles validadas no banco (CHECK constraint)
- ✅ Multi-tenant: usuários só veem/modificam seus dados
- ✅ Middleware de Request ID + Logging
- ✅ Exception handlers centralizados

### ⚠️ Melhorias futuras (opcional)
- Refresh tokens (renovar sem relogin)
- Rate limiting (evitar brute force)
- HTTPS obrigatório em produção
- Hashing de SECRET_KEY (usar HSM ou Vault)
- Auditoria de ações (tabela de logs)

---

## 📊 ROLES E PERMISSÕES

| Role        | Ver pedidos       | Criar pedidos | Deletar pedidos       |
|-------------|-------------------|---------------|-----------------------|
| **admin**   | Todos             | ✅ Sim        | Todos                 |
| **user**    | Só os seus        | ✅ Sim        | Só os seus            |
| **technician** | Só os seus     | ✅ Sim        | Só os seus            |
| **finance** | Só os seus        | ✅ Sim        | Só os seus            |

---

## 🐛 TROUBLESHOOTING

### ❌ Erro: "JWT_SECRET não configurado"
**Solução:** Crie `backend/.env` com `SECRET_KEY=sua-chave-aqui`

### ❌ Erro: "Token inválido"
**Possíveis causas:**
1. Token expirado (60 min)
2. SECRET_KEY mudou após gerar token
3. Formato errado no header (deve ser: `Authorization: Bearer TOKEN`)

**Solução:** Faça login novamente

### ❌ Erro ao logar: "Credenciais inválidas"
**Possíveis causas:**
1. Senha errada
2. Email não cadastrado
3. Hash incompatível (seed SQL vs Python)

**Solução:** Use seed Python (`python backend/seed_users.py`)

### ❌ "Você não tem permissão para deletar este pedido"
**Causa:** Tentou deletar pedido de outro usuário (e você não é admin)

**Solução:** Faça login como admin ou delete apenas seus pedidos

---

## ✅ CHECKLIST DE VALIDAÇÃO

- [x] Banco criado com `bootstrap_database.ps1`
- [x] Usuários seed criados compatíveis com bcrypt Python
- [x] API iniciada sem erros
- [x] `POST /auth/register` - Registra novo usuário
- [x] `POST /auth/login` - Retorna JWT válido
- [x] `GET /auth/me` - Com token, retorna dados do usuário
- [x] `POST /orders` - Com token, cria pedido para usuário autenticado
- [x] `GET /orders` - Admin vê todos, user vê só os seus
- [x] `DELETE /orders/{id}` - Admin deleta qualquer, user só os seus
- [x] Swagger UI funciona com autenticação (botão Authorize)

---

## 📚 PRÓXIMOS PASSOS

### ETAPA 3 (opcional - melhorias)
- [ ] Refresh tokens
- [ ] Rate limiting
- [ ] Auditoria de ações
- [ ] Testes automatizados (pytest)
- [ ] CI/CD (GitHub Actions)
- [ ] Frontend (React/Vue)

---

## 🎉 CONCLUSÃO

**ETAPA 2 = 100% FUNCIONAL** ✅

Sistema enterprise de autenticação:
- ✅ JWT robusto
- ✅ Multi-tenant
- ✅ Clean architecture (Repository → Service → Router)
- ✅ Pronto para produção (ajustando SECRET_KEY e senhas)

**Resultado:** ERP profissional, seguro e escalável! 🚀
