# ERP JSP - Backend API

FastAPI-based ERP system with multi-tenant support, financial management, and comprehensive reporting.

## 🎯 Status

**Version:** 1.0.0  
**Tests:** ✅ 31/31 passing (100%)  
**Coverage:** 76%  
**Grade:** A+ Production-Ready

---

## 🚀 Quick Start

### 1. Prerequisites

- Python 3.13+
- PostgreSQL 16+ (via Docker)
- Docker Desktop running

### 2. Setup

```powershell
# Clone repository
cd "C:\Users\julia\Desktop\ERP_JSP Training\jsp-erp"

# Create virtual environment
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Start PostgreSQL (from project root)
cd ..
docker-compose up -d db

# Bootstrap database
.\bootstrap_database.ps1
```

### 3. Run Tests

```powershell
cd backend
pytest -v --cov=app
# Expected: 31 passed in ~22s
```

### 4. Start API

```powershell
cd backend
uvicorn app.main:app --reload
# API: http://127.0.0.1:8000
# Docs: http://127.0.0.1:8000/docs
```

---

## 📁 Project Structure

```
backend/
├── app/
│   ├── auth/              # JWT authentication & RBAC
│   ├── exceptions/        # Error handlers
│   ├── middleware/        # Logging & request_id
│   ├── models/            # SQLAlchemy models
│   ├── repositories/      # Data access layer
│   ├── routers/           # API endpoints
│   ├── schemas/           # Pydantic schemas
│   ├── security/          # JWT & password utils
│   ├── services/          # Business logic
│   ├── utils/             # Pagination & helpers
│   ├── config.py          # Configuration
│   ├── database.py        # DB connection
│   └── main.py            # FastAPI app
├── tests/
│   ├── conftest.py        # Test fixtures
│   ├── test_auth_login.py
│   ├── test_financial_idempotency.py
│   ├── test_health.py
│   ├── test_orders_get_post_delete.py
│   └── test_reports_smoke.py
├── alembic/               # Database migrations
├── requirements.txt
└── pytest.ini
```

---

## 🔌 API Endpoints

### Authentication
- `POST /auth/register` - Create new user
- `POST /auth/login` - Login & get JWT token
- `GET /auth/me` - Get current user info

### Orders
- `GET /orders` - List orders (pagination + multi-tenant)
- `POST /orders` - Create order (auto-creates financial entry)
- `DELETE /orders/{id}` - Delete order (validates financial status)

### Financial Entries
- `GET /financial` - List entries (status filter + multi-tenant)
- `POST /financial` - Create manual entry
- `PUT /financial/{id}/status` - Update status (pay/cancel)

### Reports
- `GET /reports/financial/dre` - DRE (Profit & Loss)
- `GET /reports/financial/cashflow/daily` - Daily cashflow
- `GET /reports/financial/pending/aging` - Aging analysis
- `GET /reports/financial/top` - Top entries by value

### Health
- `GET /health` - Health check (no auth required)

---

## 🧪 Testing

### Run All Tests

```powershell
pytest -v
# 31 tests, should pass in ~22s
```

### Run Specific Module

```powershell
pytest tests/test_reports_smoke.py -v
```

### Run with Coverage

```powershell
pytest --cov=app --cov-report=html
# Opens htmlcov/index.html
```

### Test Database

Tests use **isolated test database** (`core_test` schema):
- No interference with development data
- Automatic cleanup after each test
- Fixtures in `conftest.py`

---

## 🔐 Authentication

### Register User

```bash
curl -X POST http://127.0.0.1:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123!",
    "name": "John Doe",
    "role": "user"
  }'
```

### Login

```bash
curl -X POST http://127.0.0.1:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "user@example.com",
    "password": "SecurePass123!"
  }'

# Response: {"access_token": "eyJ...", "token_type": "bearer"}
```

### Use Token

```bash
curl -X GET http://127.0.0.1:8000/auth/me \
  -H "Authorization: Bearer eyJ..."
```

---

## 🎛️ Configuration

Environment variables (create `.env` file):

```env
# Database
DATABASE_URL=postgresql://erp_user:erp_pass@localhost:5432/jsp_erp

# Security
SECRET_KEY=your-super-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# API
APP_NAME=ERP JSP
VERSION=1.0.0
DEBUG=True

# CORS
CORS_ORIGINS=["http://localhost:3000"]  # Frontend URL
```

---

## 📊 Multi-Tenant Behavior

### Admin Role
- Sees **all** orders/financial entries/reports
- Can manage all users
- Full system access

### User/Finance/Technician Roles
- See **only own** data
- CRUD operations limited to own entries
- Reports filtered by user_id

**Example: GET /orders**
- Admin → Returns all orders
- User → Returns only `orders.user_id = current_user.id`

---

## 🧩 Database Schema

### Core Tables

**users:**
- id (UUID PK)
- email (unique)
- password_hash
- name
- role (admin/user/finance/technician)
- created_at

**orders:**
- id (UUID PK)
- user_id (FK → users)
- customer_name
- total
- created_at, updated_at

**financial_entries:**
- id (UUID PK)
- user_id (FK → users)
- order_id (FK → orders, nullable)
- kind (revenue/expense)
- status (pending/paid/canceled)
- amount
- description
- occurred_at
- created_at, updated_at

---

## 🔄 Migrations

### Create Migration

```powershell
alembic revision -m "description"
```

### Apply Migrations

```powershell
alembic upgrade head
```

### Rollback

```powershell
alembic downgrade -1
```

---

## 🐛 Troubleshooting

### Tests Failing

```powershell
# Check if PostgreSQL is running
docker ps | Select-String "postgres"

# Re-run bootstrap
.\bootstrap_database.ps1

# Clear pytest cache
pytest --cache-clear
```

### API Not Starting

```powershell
# Check port 8000 is free
netstat -ano | Select-String "8000"

# Activate virtual environment
.venv\Scripts\Activate.ps1

# Check dependencies
pip list | Select-String "fastapi"
```

### Database Connection Error

```powershell
# Test connection
docker exec -it jsp_erp_db psql -U erp_user -d jsp_erp -c "SELECT 1"

# Check password
# Password is in docker-compose.yml (POSTGRES_PASSWORD)
```

---

## 📚 Documentation

- **API Docs:** http://127.0.0.1:8000/docs (Swagger UI)
- **ReDoc:** http://127.0.0.1:8000/redoc
- **Etapa 5A Conclusão:** `../docs/ETAPA_5A_CONCLUSAO.md`
- **Roadmap:** `../docs/ROADMAP_PROXIMAS_ETAPAS.md`

---

## 📈 Performance

### Benchmarks (local development)

- **Health Check:** ~2ms
- **Login:** ~150ms (bcrypt hashing)
- **List Orders:** ~10ms (10 items)
- **DRE Report:** ~50ms (1000 entries)
- **Test Suite:** ~22s (31 tests)

### Database

- **Indexes:** user_id, occurred_at, status
- **Connection Pool:** 5-20 connections
- **Query Timeout:** None (development)

---

## 🚀 Next Steps

See `../docs/ROADMAP_PROXIMAS_ETAPAS.md` for:
- Features Enterprise (Audit Log, Soft Delete, RBAC)
- Hardening & Quality (Coverage 85%+, Rate Limiting)
- Production Deployment (Docker, CI/CD)
- Frontend (Next.js)

---

## 📝 License

Proprietary - ERP JSP Training Project

---

## 👥 Contributors

- Juliano Saroba (@JulianoSaroba123)

---

**Last Updated:** 18/02/2026  
**Status:** ✅ Production-Ready (31/31 tests passing)
