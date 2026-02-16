# 🎨 DIAGRAMAS VISUAIS - ETAPA 2

## 📊 Visão Geral da Implementação

Este documento contém diagramas visuais para facilitar o entendimento da arquitetura de autenticação e multi-tenant implementada na ETAPA 2.

---

## 🔄 Fluxo de Autenticação (Sequence Diagram)

### Sequência completa: Registro → Login → Acesso Protegido

```mermaid
sequenceDiagram
    participant Cliente
    participant Router
    participant Service
    participant Repository
    participant Database
    participant Security

    Note over Cliente,Security: 1. REGISTRO DE USUÁRIO
    Cliente->>Router: POST /auth/register<br/>{email, password, name, role}
    Router->>Service: register(email, password, name, role)
    Service->>Repository: get_by_email(email)
    Repository->>Database: SELECT * FROM users WHERE email=?
    Database-->>Repository: null (não existe)
    Repository-->>Service: null
    Service->>Security: hash_password(password)
    Security-->>Service: password_hash (bcrypt)
    Service->>Repository: create(User)
    Repository->>Database: INSERT INTO users...
    Database-->>Repository: User criado
    Repository-->>Service: User
    Service-->>Router: User
    Router-->>Cliente: 201 Created {id, email, name, role}

    Note over Cliente,Security: 2. LOGIN E GERAÇÃO DE TOKEN
    Cliente->>Router: POST /auth/login<br/>{username=email, password}
    Router->>Service: authenticate(email, password)
    Service->>Repository: get_by_email(email)
    Repository->>Database: SELECT * FROM users WHERE email=?
    Database-->>Repository: User encontrado
    Repository-->>Service: User
    Service->>Security: verify_password(password, user.password_hash)
    Security-->>Service: true (senha correta)
    Service-->>Router: User autenticado
    Router->>Security: create_access_token(subject=user.id)
    Security-->>Router: JWT token
    Router-->>Cliente: 200 OK {access_token, user}

    Note over Cliente,Security: 3. ACESSO A ROTA PROTEGIDA
    Cliente->>Router: GET /orders<br/>Authorization: Bearer TOKEN
    Router->>Router: get_current_user(token)
    Router->>Security: decode_token(token)
    Security-->>Router: {sub: user_id, iat, exp}
    Router->>Repository: get_by_id(user_id)
    Repository->>Database: SELECT * FROM users WHERE id=?
    Database-->>Repository: User
    Repository-->>Router: User (current_user)
    Router->>Service: list_orders(user_id=current_user.id)
    Service->>Repository: list_by_user(user_id)
    Repository->>Database: SELECT * FROM orders WHERE user_id=?
    Database-->>Repository: [Orders]
    Repository-->>Service: [Orders]
    Service-->>Router: {items, total}
    Router-->>Cliente: 200 OK {items, page, total}
```

**Legenda:**
- **1. Registro**: Senha é hasheada com bcrypt antes de salvar
- **2. Login**: Verifica senha e retorna JWT com 60min de validade
- **3. Acesso**: Token é validado e user_id extraído para filtrar dados

---

## 🏗️ Arquitetura Multi-tenant (Component Diagram)

### Visão completa dos componentes e suas interações

```mermaid
graph TB
    subgraph "Cliente"
        C1[Admin Browser]
        C2[User Browser]
    end

    subgraph "FastAPI Backend"
        subgraph "Middleware"
            M1[RequestID]
            M2[Logging]
            M3[CORS]
        end
        
        subgraph "Auth Module"
            R1[Router<br/>/auth/register<br/>/auth/login<br/>/auth/me]
            S1[AuthService<br/>register<br/>authenticate]
            RP1[UserRepository<br/>get_by_email<br/>create]
            SEC[Security<br/>hash_password<br/>verify_password<br/>JWT]
        end
        
        subgraph "Orders Module"
            R2[Router<br/>GET /orders<br/>POST /orders<br/>DELETE /orders]
            S2[OrderService<br/>list_orders<br/>create_order<br/>delete_order]
            RP2[OrderRepository<br/>list_by_user<br/>create<br/>delete_by_id]
        end
        
        DEP[get_current_user<br/>Dependency]
    end
    
    subgraph "PostgreSQL"
        DB[(Database: jsp_erp)]
        T1[core.users<br/>id UUID PK<br/>email UNIQUE<br/>password_hash<br/>role<br/>is_active]
        T2[core.orders<br/>id UUID PK<br/>user_id UUID FK<br/>description<br/>total<br/>created_at]
    end

    C1 -->|POST /auth/login| M1
    C2 -->|POST /auth/login| M1
    M1 --> M2
    M2 --> M3
    M3 --> R1
    
    C1 -->|GET /orders<br/>Bearer TOKEN_ADMIN| DEP
    C2 -->|GET /orders<br/>Bearer TOKEN_USER| DEP
    
    R1 --> S1
    S1 --> RP1
    S1 --> SEC
    RP1 --> T1
    
    DEP --> SEC
    DEP --> RP1
    DEP -->|current_user| R2
    
    R2 --> S2
    S2 --> RP2
    RP2 --> T2
    
    T2 -.->|FK user_id| T1
    
    style C1 fill:#e1f5ff
    style C2 fill:#fff4e1
    style DEP fill:#ffe1e1
    style SEC fill:#e1ffe1
    style T1 fill:#f0f0f0
    style T2 fill:#f0f0f0
```

**Componentes principais:**
- **get_current_user**: Dependency que valida token e injeta usuário autenticado
- **Security**: Módulo centralizado de criptografia (bcrypt) e JWT
- **Repositories**: Camada de acesso a dados (isolamento SQL)
- **Services**: Lógica de negócio e validações
- **Routers**: Controllers HTTP (FastAPI)

---

## 🔐 Fluxo Multi-tenant (Flowchart)

### Decisão de autorização e filtro de dados por role

```mermaid
flowchart TD
    Start([Cliente faz request<br/>GET /orders]) --> HasToken{Token JWT<br/>presente?}
    
    HasToken -->|Não| Unauthorized[❌ 401 Unauthorized<br/>'Not authenticated']
    HasToken -->|Sim| DecodeToken[Decodificar Token JWT]
    
    DecodeToken --> ValidToken{Token<br/>válido?}
    ValidToken -->|Não expirado<br/>Assinatura OK| GetUser[Buscar User no DB<br/>por user_id do token]
    ValidToken -->|Expirado ou<br/>inválido| Unauthorized
    
    GetUser --> UserExists{User<br/>existe?}
    UserExists -->|Não| Unauthorized
    UserExists -->|Sim| IsActive{User<br/>ativo?}
    
    IsActive -->|Não| Unauthorized
    IsActive -->|Sim| SetCurrentUser[✅ current_user definido]
    
    SetCurrentUser --> CheckRole{current_user.role<br/>é admin?}
    
    CheckRole -->|Sim| ListAll[Listar TODOS os pedidos<br/>SELECT * FROM orders]
    CheckRole -->|Não| ListOwn[Listar SÓ os pedidos do user<br/>SELECT * FROM orders<br/>WHERE user_id = current_user.id]
    
    ListAll --> Return200[✅ 200 OK<br/>items, total]
    ListOwn --> Return200
    
    Return200 --> End([Response])
    Unauthorized --> End
    
    style Start fill:#e1f5ff
    style HasToken fill:#fff4e1
    style ValidToken fill:#fff4e1
    style UserExists fill:#fff4e1
    style IsActive fill:#fff4e1
    style CheckRole fill:#ffe1f5
    style SetCurrentUser fill:#e1ffe1
    style ListAll fill:#e1f5e1
    style ListOwn fill:#fff9e1
    style Return200 fill:#e1ffe1
    style Unauthorized fill:#ffe1e1
    style End fill:#f0f0f0
```

**Pontos de validação:**
1. Token presente no header?
2. Token válido (não expirado, assinatura OK)?
3. User existe no banco?
4. User está ativo?
5. Role determina filtro de dados

---

## 📊 Matriz de Permissões

### Controle de acesso por role

| Operação | Endpoint | Admin | User | Technician | Finance |
|----------|----------|-------|------|------------|---------|
| **Autenticação** |
| Registrar | `POST /auth/register` | ✅ | ✅ | ✅ | ✅ |
| Login | `POST /auth/login` | ✅ | ✅ | ✅ | ✅ |
| Ver perfil | `GET /auth/me` | ✅ | ✅ | ✅ | ✅ |
| **Pedidos - Leitura** |
| Listar pedidos | `GET /orders` | 🌐 Todos | 🔒 Só seus | 🔒 Só seus | 🔒 Só seus |
| Ver pedido específico | `GET /orders/{id}` | ✅ Qualquer | 🔒 Só seus | 🔒 Só seus | 🔒 Só seus |
| **Pedidos - Escrita** |
| Criar pedido | `POST /orders` | ✅ | ✅ | ✅ | ✅ |
| Atualizar pedido | `PUT /orders/{id}` | ✅ Qualquer | 🔒 Só seus | 🔒 Só seus | 🔒 Só seus |
| Deletar pedido | `DELETE /orders/{id}` | ✅ Qualquer | 🔒 Só seus | 🔒 Só seus | 🔒 Só seus |

**Legenda:**
- ✅ = Acesso total
- 🌐 = Vê todos os registros
- 🔒 = Vê/modifica apenas registros próprios (user_id = current_user.id)

---

## 🔑 Estrutura do Token JWT

### Payload decodificado

```json
{
  "sub": "550e8400-e29b-41d4-a716-446655440000",  // user.id (UUID)
  "iat": 1676476800,                               // Issued At (timestamp)
  "exp": 1676480400                                // Expiration (timestamp)
}
```

**Validações realizadas:**
1. Assinatura HMAC-SHA256 com SECRET_KEY
2. Expiração (exp > now)
3. User existe no banco (sub = user.id)
4. User está ativo (is_active = true)

---

## 🗄️ Modelo de Dados (ER Diagram)

```
┌─────────────────────────┐
│      core.users         │
├─────────────────────────┤
│ 🔑 id (UUID)            │
│    name (VARCHAR)       │
│    email (VARCHAR) UK   │
│    password_hash (TEXT) │
│    role (VARCHAR)       │
│    is_active (BOOLEAN)  │
│    created_at (TIMESTAMP)│
└──────────┬──────────────┘
           │
           │ 1:N
           │
           ▼
┌─────────────────────────┐
│     core.orders         │
├─────────────────────────┤
│ 🔑 id (UUID)            │
│ 🔗 user_id (UUID) FK    │
│    description (TEXT)   │
│    total (NUMERIC)      │
│    created_at (TIMESTAMP)│
└─────────────────────────┘
```

**Constraints:**
- `users.email` - UNIQUE
- `users.role` - CHECK IN ('admin', 'user', 'technician', 'finance')
- `orders.user_id` - FK REFERENCES users(id) ON DELETE CASCADE

---

## 🔄 Ciclo de Vida do Token

```mermaid
stateDiagram-v2
    [*] --> Login: POST /auth/login
    Login --> TokenCriado: JWT gerado
    TokenCriado --> TokenValido: Dentro de 60min
    TokenValido --> TokenExpirado: Após 60min
    TokenExpirado --> Login: Fazer login novamente
    TokenValido --> [*]: Logout (descarta token)
    
    note right of TokenCriado
        Token contém:
        - user_id (sub)
        - issued_at (iat)
        - expiration (exp)
    end note
    
    note right of TokenValido
        Cliente armazena:
        - localStorage
        - sessionStorage
        - Cookie (HttpOnly)
    end note
```

**Melhorias futuras (ETAPA 3):**
- Refresh tokens (renovar sem relogin)
- Blacklist de tokens revogados
- Múltiplas sessões simultâneas

---

## 🛡️ Camadas de Segurança

```
┌─────────────────────────────────────────┐
│          1. TRANSPORTE (HTTPS)          │ ← Produção
├─────────────────────────────────────────┤
│      2. CORS / Rate Limiting            │ ← FastAPI Middleware
├─────────────────────────────────────────┤
│   3. AUTENTICAÇÃO (JWT + Bcrypt)        │ ← Esta implementação
├─────────────────────────────────────────┤
│  4. AUTORIZAÇÃO (Multi-tenant + Roles)  │ ← Esta implementação
├─────────────────────────────────────────┤
│       5. VALIDAÇÃO (Pydantic)           │ ← Schemas
├─────────────────────────────────────────┤
│    6. BANCO (Constraints + Índices)     │ ← PostgreSQL
└─────────────────────────────────────────┘
```

**Implementado na ETAPA 2:** ✅ Camadas 3, 4, 5, 6  
**Para produção:** Adicionar camadas 1, 2

---

## 📈 Performance e Escalabilidade

### Otimizações implementadas:

1. **Índices no banco:**
   ```sql
   CREATE INDEX idx_users_email ON core.users (email);
   CREATE INDEX idx_users_role ON core.users (role);
   CREATE INDEX idx_users_is_active ON core.users (is_active);
   ```

2. **Connection pooling:**
   - SQLAlchemy engine com `pool_pre_ping=True`
   - Sessões descartadas após uso (Dependency `get_db`)

3. **Bcrypt rounds:**
   - Default: 12 rounds (bom equilíbrio segurança/performance)

4. **JWT stateless:**
   - Sem consulta ao banco para validar (só decodificar)
   - Consulta única para pegar User após validação

---

## 🎯 Casos de Uso Visuais

### Caso 1: Admin visualiza todos os pedidos

```
Admin Login
    ↓
Token JWT (sub=admin_id, role=admin)
    ↓
GET /orders
    ↓
get_current_user → admin
    ↓
CheckRole(admin) → TRUE
    ↓
SELECT * FROM orders  ← SEM FILTRO
    ↓
Return ALL orders
```

### Caso 2: User visualiza seus pedidos

```
User Login
    ↓
Token JWT (sub=user_id, role=user)
    ↓
GET /orders
    ↓
get_current_user → user
    ↓
CheckRole(admin) → FALSE
    ↓
SELECT * FROM orders WHERE user_id = user.id  ← COM FILTRO
    ↓
Return ONLY user's orders
```

---

## 🚀 Deploy - Arquitetura de Produção (Future)

```
┌─────────────────┐
│   Load Balancer │  ← Nginx/Traefik
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
┌───▼───┐ ┌──▼────┐
│ API 1 │ │ API 2 │  ← Múltiplas instâncias FastAPI
└───┬───┘ └──┬────┘
    │         │
    └────┬────┘
         │
    ┌────▼────┐
    │   DB    │  ← PostgreSQL (RDS/Managed)
    └─────────┘
```

**Considerações:**
- JWT é stateless → Escalável horizontalmente
- Sessões não necessárias (sem Redis para isso)
- Cada instância da API é independente

---

**Veja também:**
- [`ETAPA_2_CONCLUSAO.md`](ETAPA_2_CONCLUSAO.md) - Documentação completa
- [`ETAPA_2_GUIA_RAPIDO.md`](ETAPA_2_GUIA_RAPIDO.md) - Start rápido
- [`COMANDOS_TESTE_ETAPA2.md`](COMANDOS_TESTE_ETAPA2.md) - Testes práticos
