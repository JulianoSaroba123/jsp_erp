"""
Teste automatizado para verificar a criação de Ordem de Serviço com itens.

Este teste valida que a tabela service_order_items existe e funciona corretamente.
"""
import os
import sys
from uuid import uuid4
from decimal import Decimal
from datetime import datetime, date

# Configurar PYTHONPATH
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Importar todos os models para garantir inicialização correta
from app.database import Base
from app.models import *  # Importar todos os models
from app.models.service_order import ServiceOrder, ServiceOrderItem
from app.models.customer import Customer
from app.models.user import User

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("❌ DATABASE_URL não configurada no .env")
    sys.exit(1)

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)

print("=" * 70)
print("TESTE: CRIAR ORDEM DE SERVIÇO COM ITENS")
print("=" * 70)

# Iniciar sessão
db = SessionLocal()

try:
    # 1. Buscar ou criar cliente de teste
    print("\n1️⃣ Buscando cliente de teste...")
    customer = db.query(Customer).filter(Customer.deleted_at.is_(None)).first()
    
    if not customer:
        print("   ⚠️ Nenhum cliente encontrado. Criando cliente de teste...")
        customer = Customer(
            id=uuid4(),
            name="Cliente Teste OS",
            document="00000000000",
            customer_type="individual",
            status="active"
        )
        db.add(customer)
        db.commit()
        db.refresh(customer)
        print(f"   ✅ Cliente criado: {customer.name} (ID: {customer.id})")
    else:
        print(f"   ✅ Cliente encontrado: {customer.name} (ID: {customer.id})")
    
    # 2. Buscar usuário de teste
    print("\n2️⃣ Buscando usuário de teste...")
    user = db.query(User).first()
    
    if not user:
        print("   ❌ Nenhum usuário encontrado no banco")
        sys.exit(1)
    else:
        print(f"   ✅ Usuário encontrado: {user.email} (ID: {user.id})")
    
    # 3. Criar Ordem de Serviço
    print("\n3️⃣ Criando Ordem de Serviço...")
    
    service_order = ServiceOrder(
        id=uuid4(),
        number=f"OS-TEST-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        customer_id=customer.id,
        user_id=user.id,
        title="Ordem de Serviço de Teste",
        description="Teste automatizado de criação de OS com itens",
        order_type="comercial",
        status="pendente",
        priority="normal",
        opening_date=date.today(),
        service_amount=Decimal("0.00"),
        parts_amount=Decimal("0.00"),
        discount_amount=Decimal("0.00"),
        total_amount=Decimal("0.00")
    )
    
    db.add(service_order)
    db.commit()
    db.refresh(service_order)
    
    print(f"   ✅ Ordem de Serviço criada: {service_order.number} (ID: {service_order.id})")
    
    # 4. Adicionar itens de serviço
    print("\n4️⃣ Adicionando itens de serviço...")
    
    items_data = [
        {
            "description": "Manutenção preventiva",
            "service_type": "hora",
            "quantity": Decimal("2.00"),
            "unit_price": Decimal("150.00"),
            "total_price": Decimal("300.00")
        },
        {
            "description": "Instalação de equipamento",
            "service_type": "fechado",
            "quantity": Decimal("1.00"),
            "unit_price": Decimal("500.00"),
            "total_price": Decimal("500.00")
        },
        {
            "description": "Suporte técnico",
            "service_type": "dia",
            "quantity": Decimal("0.50"),
            "unit_price": Decimal("800.00"),
            "total_price": Decimal("400.00")
        }
    ]
    
    created_items = []
    for idx, item_data in enumerate(items_data, 1):
        item = ServiceOrderItem(
            id=uuid4(),
            service_order_id=service_order.id,
            description=item_data["description"],
            service_type=item_data["service_type"],
            quantity=item_data["quantity"],
            unit_price=item_data["unit_price"],
            total_price=item_data["total_price"]
        )
        db.add(item)
        created_items.append(item)
        print(f"   ✅ Item {idx}: {item.description} - {item.service_type} - R$ {item.total_price}")
    
    db.commit()
    
    # 5. Atualizar total da OS
    total_services = sum(item.total_price for item in created_items)
    service_order.service_amount = total_services
    service_order.total_amount = total_services
    db.commit()
    
    print(f"\n   💰 Total da OS atualizado: R$ {service_order.total_amount}")
    
    # 6. Verificar itens salvos
    print("\n5️⃣ Verificando itens salvos no banco...")
    
    saved_items = db.query(ServiceOrderItem).filter(
        ServiceOrderItem.service_order_id == service_order.id
    ).all()
    
    print(f"   ✅ Total de itens salvos: {len(saved_items)}")
    
    for idx, item in enumerate(saved_items, 1):
        print(f"   📋 Item {idx}:")
        print(f"      - ID: {item.id}")
        print(f"      - Descrição: {item.description}")
        print(f"      - Tipo: {item.service_type}")
        print(f"      - Quantidade: {item.quantity}")
        print(f"      - Valor Unitário: R$ {item.unit_price}")
        print(f"      - Valor Total: R$ {item.total_price}")
        print(f"      - Criado em: {item.created_at}")
    
    # 7. Testar relacionamento
    print("\n6️⃣ Testando relacionamento ServiceOrder.items...")
    
    db.refresh(service_order)
    
    if hasattr(service_order, 'items'):
        print(f"   ✅ Relacionamento 'items' existe")
        print(f"   ✅ Total de itens via relacionamento: {len(service_order.items)}")
        
        for idx, item in enumerate(service_order.items, 1):
            print(f"   📋 Item {idx} (via relacionamento): {item.description}")
    else:
        print("   ⚠️ Relacionamento 'items' não encontrado")
    
    # 8. Resultado final
    print("\n" + "=" * 70)
    print("✅ TESTE CONCLUÍDO COM SUCESSO!")
    print("=" * 70)
    print(f"📄 Ordem de Serviço: {service_order.number}")
    print(f"👤 Cliente: {customer.name}")
    print(f"📋 Total de itens: {len(saved_items)}")
    print(f"💰 Valor total: R$ {service_order.total_amount}")
    print("=" * 70)
    
    # Limpar teste (opcional - comentar se quiser manter os dados)
    print("\n🗑️ Limpando dados de teste...")
    
    for item in saved_items:
        db.delete(item)
    
    db.delete(service_order)
    db.commit()
    
    print("   ✅ Dados de teste removidos com sucesso")

except Exception as e:
    print(f"\n❌ ERRO no teste: {e}")
    import traceback
    traceback.print_exc()
    db.rollback()
    sys.exit(1)

finally:
    db.close()
