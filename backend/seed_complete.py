"""
Script para popular banco de dados com dados de exemplo completos
- Usuários
- Produtos  
- Clientes
- Lançamentos Financeiros
- Pedidos

Uso:
    python seed_complete.py
"""
import os
import sys
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4

# Adiciona o diretório backend ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models.user import User
from app.models.product import Product
from app.models.customer import Customer
from app.models.financial_entry import FinancialEntry
from app.security.password import hash_password


def get_db_url():
    """Lê DATABASE_URL do .env"""
    from dotenv import load_dotenv
    load_dotenv()
    return os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5433/erp_db")


def seed_complete_data():
    """Popula banco com dados completos"""
    db_url = get_db_url()
    engine = create_engine(db_url)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        print("🌱 Iniciando seed completo...\n")
        
        # 1. USUÁRIOS
        print("👥 Criando usuários...")
        users_data = [
            {"name": "Admin System", "email": "admin@jsp.com", "role": "admin"},
            {"name": "João Silva", "email": "joao@jsp.com", "role": "user"},
            {"name": "Maria Santos", "email": "maria@jsp.com", "role": "finance"},
            {"name": "Carlos Oliveira", "email": "carlos@jsp.com", "role": "technician"},
        ]
        
        users = []
        password_hash = hash_password("123456")
        
        for user_data in users_data:
            existing = db.query(User).filter(User.email == user_data["email"]).first()
            if existing:
                print(f"  ⚠️  {user_data['email']} já existe")
                users.append(existing)
            else:
                user = User(
                    name=user_data["name"],
                    email=user_data["email"],
                    password_hash=password_hash,
                    role=user_data["role"],
                    is_active=True
                )
                db.add(user)
                db.flush()
                users.append(user)
                print(f"  ✅ {user_data['email']} criado")
        
        db.commit()
        admin_user = users[0]
        
        # 2. PRODUTOS
        print("\n📦 Criando produtos...")
        products_data = [
            {"name": "Notebook Dell Inspiron", "description": "i5, 8GB RAM, 256GB SSD", "cost": "2200.00", "sale": "2999.90", "stock": 15, "category": "informatica"},
            {"name": "Mouse Logitech MX", "description": "Wireless, Ergonômico", "cost": "180.00", "sale": "299.90", "stock": 50, "category": "perifericos"},
            {"name": "Teclado Mecânico RGB", "description": "Switch Blue, RGB", "cost": "280.00", "sale": "459.90", "stock": 30, "category": "perifericos"},
            {"name": "Monitor LG 24pol", "description": "Full HD, IPS", "cost": "600.00", "sale": "899.90", "stock": 20, "category": "informatica"},
            {"name": "Headset Gamer", "description": "7.1 Virtual, RGB", "cost": "150.00", "sale": "249.90", "stock": 40, "category": "perifericos"},
            {"name": "WebCam Full HD", "description": "1080p, Microfone Integrado", "cost": "120.00", "sale": "199.90", "stock": 25, "category": "perifericos"},
            {"name": "SSD Kingston 500GB", "description": "NVMe, 3500MB/s", "cost": "220.00", "sale": "349.90", "stock": 35, "category": "hardware"},
            {"name": "Memória RAM 16GB", "description": "DDR4, 3200MHz", "cost": "180.00", "sale": "299.90", "stock": 45, "category": "hardware"},
        ]
        
        products = []
        for prod_data in products_data:
            existing = db.query(Product).filter(Product.name == prod_data["name"]).first()
            if existing:
                print(f"  ⚠️  {prod_data['name']} já existe")
                products.append(existing)
            else:
                product = Product(
                    user_id=admin_user.id,
                    name=prod_data["name"],
                    description=prod_data["description"],
                    cost_price=Decimal(prod_data["cost"]),
                    sale_price=Decimal(prod_data["sale"]),
                    stock_qty=Decimal(prod_data["stock"]),
                    category=prod_data["category"],
                    active=True
                )
                db.add(product)
                db.flush()
                products.append(product)
                print(f"  ✅ {prod_data['name']} criado")
        
        db.commit()
        
        # 3. CLIENTES
        print("\n👨‍💼 Criando clientes...")
        customers_data = [
            {"name": "Empresa ABC Ltda", "email": "contato@abc.com.br", "phone": "(11) 3333-4444", "cpf_cnpj": "12345678000190"},
            {"name": "Tech Solutions SA", "email": "vendas@techsolutions.com", "phone": "(11) 98765-4321", "cpf_cnpj": "98765432000110"},
            {"name": "Comércio XYZ", "email": "compras@xyz.com.br", "phone": "(21) 2222-3333", "cpf_cnpj": "11222333000144"},
            {"name": "José da Silva", "email": "jose.silva@email.com", "phone": "(11) 99999-8888", "cpf_cnpj": "12345678900"},
            {"name": "Maria Oliveira", "email": "maria.oliveira@email.com", "phone": "(11) 97777-6666", "cpf_cnpj": "98765432100"},
        ]
        
        customers = []
        for cust_data in customers_data:
            # Verifica por email (pode haver duplicatas em clientes)
            existing = db.query(Customer).filter(Customer.email == cust_data["email"]).first()
            if existing:
                print(f"  ⚠️  {cust_data['name']} já existe")
                customers.append(existing)
            else:
                customer = Customer(
                    name=cust_data["name"],
                    email=cust_data["email"],
                    phone=cust_data["phone"],
                    cpf_cnpj=cust_data.get("cpf_cnpj"),
                    status='active'
                )
                db.add(customer)
                db.flush()
                customers.append(customer)
                print(f"  ✅ {cust_data['name']} criado")
        
        db.commit()
        
        # 4. LANÇAMENTOS FINANCEIROS
        print("\n💰 Criando lançamentos financeiros...")
        
        # Receitas (últimos 30 dias)
        revenues = [
            {"desc": "Venda Notebook Dell - Empresa ABC", "amount": "2999.90", "days_ago": 2, "status": "paid"},
            {"desc": "Venda Mouse + Teclado - Tech Solutions", "amount": "759.80", "days_ago": 5, "status": "paid"},
            {"desc": "Venda Monitor LG - José Silva", "amount": "899.90", "days_ago": 7, "status": "paid"},
            {"desc": "Venda SSD + RAM - Comércio XYZ", "amount": "649.80", "days_ago": 10, "status": "pending"},
            {"desc": "Venda Headset - Maria Oliveira", "amount": "249.90", "days_ago": 12, "status": "paid"},
            {"desc": "Venda WebCam - Empresa ABC", "amount": "199.90", "days_ago": 15, "status": "paid"},
            {"desc": "Venda Múltiplos Produtos - Tech Solutions", "amount": "4500.00", "days_ago": 20, "status": "pending"},
        ]
        
        total_revenue = Decimal("0")
        for rev_data in revenues:
            occurred_at = datetime.now() - timedelta(days=rev_data["days_ago"])
            entry = FinancialEntry(
                user_id=admin_user.id,
                kind="revenue",
                status=rev_data["status"],
                amount=Decimal(rev_data["amount"]),
                description=rev_data["desc"],
                occurred_at=occurred_at,
                order_id=None  # Manual
            )
            db.add(entry)
            total_revenue += Decimal(rev_data["amount"])
            status_icon = "✅" if rev_data["status"] == "paid" else "⏳"
            print(f"  {status_icon} Receita: {rev_data['desc'][:50]}... R$ {rev_data['amount']}")
        
        # Despesas (últimos 30 dias)
        expenses = [
            {"desc": "Compra de estoque - Fornecedor A", "amount": "5000.00", "days_ago": 3, "status": "paid"},
            {"desc": "Aluguel do escritório - Março 2026", "amount": "3500.00", "days_ago": 1, "status": "paid"},
            {"desc": "Energia elétrica - Março 2026", "amount": "450.00", "days_ago": 5, "status": "paid"},
            {"desc": "Internet empresarial", "amount": "200.00", "days_ago": 6, "status": "paid"},
            {"desc": "Manutenção equipamentos", "amount": "800.00", "days_ago": 8, "status": "pending"},
            {"desc": "Material de escritório", "amount": "350.00", "days_ago": 14, "status": "paid"},
            {"desc": "Frete e logística", "amount": "600.00", "days_ago": 18, "status": "paid"},
        ]
        
        total_expense = Decimal("0")
        for exp_data in expenses:
            occurred_at = datetime.now() - timedelta(days=exp_data["days_ago"])
            entry = FinancialEntry(
                user_id=admin_user.id,
                kind="expense",
                status=exp_data["status"],
                amount=Decimal(exp_data["amount"]),
                description=exp_data["desc"],
                occurred_at=occurred_at,
                order_id=None  # Manual
            )
            db.add(entry)
            total_expense += Decimal(exp_data["amount"])
            status_icon = "✅" if exp_data["status"] == "paid" else "⏳"
            print(f"  {status_icon} Despesa: {exp_data['desc'][:50]}... R$ {exp_data['amount']}")
        
        db.commit()
        
        # RESUMO
        print("\n" + "="*60)
        print("✅ SEED COMPLETO!")
        print("="*60)
        print(f"👥 Usuários:   {len(users)}")
        print(f"📦 Produtos:   {len(products)}")
        print(f"👨‍💼 Clientes:   {len(customers)}")
        print(f"💰 Lançamentos: {len(revenues) + len(expenses)}")
        print(f"   - Receitas: {len(revenues)} (Total: R$ {total_revenue:.2f})")
        print(f"   - Despesas: {len(expenses)} (Total: R$ {total_expense:.2f})")
        print(f"   - Saldo:    R$ {(total_revenue - total_expense):.2f}")
        print("="*60)
        print("\n🔐 Login padrão:")
        print("   Email:    admin@jsp.com")
        print("   Senha:    123456")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    seed_complete_data()
