"""
Schemas Pydantic para Service Orders (Ordens de Serviço).
"""

from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime, date, time
from typing import Optional, Literal, List
from decimal import Decimal


# ==================== ServiceOrderItem Schemas ====================

class ServiceOrderItemCreate(BaseModel):
    """Schema para criação de item de serviço."""
    description: str = Field(..., min_length=1, max_length=200, description="Descrição do serviço")
    service_type: Literal['hora', 'dia', 'fechado'] = Field('hora', description="Tipo: hora, dia ou fechado")
    quantity: Decimal = Field(1.00, ge=0, description="Quantidade")
    unit: str = Field('un', min_length=1, max_length=20, description="Unidade")
    unit_price: Decimal = Field(0.00, ge=0, description="Valor unitário")
    total_price: Decimal = Field(0.00, ge=0, description="Valor total")
    technician_notes: Optional[str] = Field(None, description="Notas do técnico")


class ServiceOrderItemUpsert(ServiceOrderItemCreate):
    """Schema para sincronizar item de serviço em update de OS."""
    id: Optional[UUID] = None


class ServiceOrderItemOut(BaseModel):
    """Schema de saída de item de serviço."""
    id: UUID
    service_order_id: UUID
    description: str
    service_type: str
    quantity: Decimal
    unit: str
    unit_price: Decimal
    total_price: Decimal
    technician_notes: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


# ==================== ServiceOrderProduct Schemas ====================

class ServiceOrderProductCreate(BaseModel):
    """Schema para criação de produto utilizado."""
    product_id: Optional[UUID] = Field(None, description="ID do produto cadastrado (opcional)")
    product_name: Optional[str] = Field(None, max_length=200, description="Nome do produto")
    description: str = Field(..., min_length=1, max_length=200, description="Descrição do produto/peça")
    quantity: Decimal = Field(1.000, ge=0, description="Quantidade")
    unit_price: Decimal = Field(0.00, ge=0, description="Valor unitário")
    total_price: Decimal = Field(0.00, ge=0, description="Valor total")


class ServiceOrderProductUpsert(ServiceOrderProductCreate):
    """Schema para sincronizar produto/peça em update de OS."""
    id: Optional[UUID] = None


class ServiceOrderProductOut(BaseModel):
    """Schema de saída de produto utilizado."""
    id: UUID
    service_order_id: UUID
    product_id: Optional[UUID]
    product_name: Optional[str]
    description: str
    quantity: Decimal
    unit_price: Decimal
    total_price: Decimal
    created_at: datetime

    model_config = {"from_attributes": True}


# ==================== ServiceOrderInstallment Schemas ====================

class ServiceOrderInstallmentCreate(BaseModel):
    """Schema para criação de parcela."""
    installment_number: int = Field(..., ge=1, description="Número da parcela")
    due_date: date = Field(..., description="Data de vencimento")
    amount: Decimal = Field(..., gt=0, description="Valor da parcela")
    status: Literal['pending', 'paid', 'overdue', 'canceled'] = Field('pending', description="Status da parcela")
    paid: bool = Field(False, description="Pago?")
    payment_date: Optional[date] = Field(None, description="Data do pagamento")


class ServiceOrderInstallmentUpsert(ServiceOrderInstallmentCreate):
    """Schema para sincronizar parcela em update de OS."""
    id: Optional[UUID] = None


class ServiceOrderInstallmentOut(BaseModel):
    """Schema de saída de parcela."""
    id: UUID
    service_order_id: UUID
    installment_number: int
    due_date: date
    amount: Decimal
    status: str
    paid: bool
    payment_date: Optional[date]
    created_at: datetime

    model_config = {"from_attributes": True}


class ServiceOrderInstallmentUpdate(BaseModel):
    """Schema para atualização de parcela."""
    installment_number: Optional[int] = Field(None, ge=1)
    due_date: Optional[date] = None
    amount: Optional[Decimal] = Field(None, gt=0)
    status: Optional[Literal['pending', 'paid', 'overdue', 'canceled']] = None
    paid: Optional[bool] = None
    payment_date: Optional[date] = None


class ServiceOrderEquipmentCreate(BaseModel):
    equipment_name: str = Field(..., min_length=1, max_length=200)
    brand: Optional[str] = Field(None, max_length=100)
    model: Optional[str] = Field(None, max_length=100)
    serial_number: Optional[str] = Field(None, max_length=100)
    accessories: Optional[str] = None
    defect_reported: Optional[str] = None
    technical_diagnosis: Optional[str] = None


class ServiceOrderEquipmentUpsert(ServiceOrderEquipmentCreate):
    id: Optional[UUID] = None


class ServiceOrderEquipmentOut(BaseModel):
    id: UUID
    service_order_id: UUID
    equipment_name: str
    brand: Optional[str]
    model: Optional[str]
    serial_number: Optional[str]
    accessories: Optional[str]
    defect_reported: Optional[str]
    technical_diagnosis: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


# ==================== ServiceOrderAttachment Schemas ====================

class ServiceOrderAttachmentCreate(BaseModel):
    """Schema para criação de anexo."""
    original_filename: str = Field(..., max_length=255)
    stored_filename: str = Field(..., max_length=255)
    file_type: str = Field(..., max_length=50)
    mime_type: Optional[str] = Field(None, max_length=100)
    file_size: Optional[int] = None
    file_path: Optional[str] = Field(None, max_length=500)


class ServiceOrderAttachmentOut(BaseModel):
    """Schema de saída de anexo."""
    id: UUID
    service_order_id: UUID
    original_filename: str
    stored_filename: str
    file_type: str
    mime_type: Optional[str]
    file_size: Optional[int]
    file_path: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


# ==================== ServiceOrder Main Schemas ====================

class ServiceOrderCreate(BaseModel):
    """Schema para criação de ordem de serviço."""
    # O número será gerado automaticamente (não incluir no create)
    code: Optional[str] = Field(None, max_length=20, description="Código externo da OS")
    customer_id: UUID = Field(..., description="ID do cliente")
    
    # Tipo de OS
    order_type: Literal['comercial', 'operacional'] = Field(
        'comercial',
        description="Tipo da OS: 'comercial' (com valores) ou 'operacional' (sem valores)"
    )
    service_type: Optional[str] = Field(None, max_length=100, description="Tipo de serviço")
    
    # Proposta vinculada (opcional)
    proposal_id: Optional[UUID] = Field(None, description="ID da proposta vinculada")
    
    # Local
    location: Optional[str] = Field(None, max_length=200, description="Local do serviço")
    
    # Dados básicos
    title: str = Field(..., min_length=1, max_length=200, description="Título da OS")
    description: Optional[str] = Field(None, description="Descrição detalhada")
    technical_report: Optional[str] = Field(None, description="Laudo técnico")
    observations: Optional[str] = Field(None, description="Observações")
    client_name: Optional[str] = Field(None, max_length=200)
    client_document: Optional[str] = Field(None, max_length=30)
    client_phone: Optional[str] = Field(None, max_length=30)
    client_email: Optional[str] = Field(None, max_length=255)
    client_address: Optional[str] = None
    
    # Solicitação
    requester: Optional[str] = Field(None, max_length=200, description="Nome do solicitante")
    problem_description: Optional[str] = Field(None, description="Problema relatado")
    
    # Status e prioridade
    status: Literal['draft', 'open', 'in_progress', 'waiting_parts', 'completed', 'canceled', 'pendente', 'em_execucao', 'finalizada', 'cancelada'] = Field(
        'pendente', 
        description="Status da OS"
    )
    priority: Literal['low', 'medium', 'high', 'urgent', 'baixa', 'normal', 'alta', 'urgente'] = Field(
        'normal', 
        description="Prioridade"
    )
    
    # Datas
    opening_date: Optional[date] = Field(None, description="Data de abertura (padrão: hoje)")
    expected_date: Optional[date] = Field(None, description="Data prevista")
    scheduled_date: Optional[date] = Field(None, description="Data agendada")
    start_date: Optional[datetime] = Field(None, description="Data/hora de início")
    completed_date: Optional[date] = Field(None, description="Data de conclusão")
    completion_date: Optional[datetime] = Field(None, description="Data/hora de conclusão")
    
    # Responsável
    technician: Optional[str] = Field(None, max_length=100, description="Técnico responsável")
    
    # Equipamento
    equipment: Optional[str] = Field(None, max_length=200, description="Equipamento")
    brand_model: Optional[str] = Field(None, max_length=200, description="Marca/Modelo")
    serial_number: Optional[str] = Field(None, max_length=100, description="Número de série")
    
    # Descrições técnicas
    reported_defect: Optional[str] = Field(None, description="Defeito relatado")
    technical_diagnosis: Optional[str] = Field(None, description="Diagnóstico técnico")
    solution: Optional[str] = Field(None, description="Solução aplicada")
    notes: Optional[str] = Field(None, description="Observações gerais")
    
    # Controle de tempo
    start_time: Optional[time] = Field(None, description="Hora inicial")
    end_time: Optional[time] = Field(None, description="Hora final")
    total_hours: Optional[str] = Field(None, max_length=20, description="Total de horas")
    morning_entry_time: Optional[time] = Field(None, description="Entrada pela manhã")
    lunch_exit_time: Optional[time] = Field(None, description="Saída para almoço")
    lunch_return_time: Optional[time] = Field(None, description="Retorno do almoço")
    evening_exit_time: Optional[time] = Field(None, description="Saída no fim do expediente")
    overtime_entry_time: Optional[time] = Field(None, description="Entrada em hora extra")
    overtime_exit_time: Optional[time] = Field(None, description="Saída em hora extra")
    regular_hours: Optional[Decimal] = Field(None, ge=0, description="Horas normais")
    overtime_hours: Optional[Decimal] = Field(None, ge=0, description="Horas extras")
    lunch_break_minutes: Optional[int] = Field(None, ge=0, description="Intervalo de almoço em minutos")
    
    # Controle de KM
    initial_km: Optional[int] = Field(None, ge=0, description="KM inicial")
    final_km: Optional[int] = Field(None, ge=0, description="KM final")
    total_km: Optional[str] = Field(None, max_length=20, description="Total KM")
    
    # Valores
    service_amount: Decimal = Field(0.00, ge=0, description="Valor de serviços")
    parts_amount: Decimal = Field(0.00, ge=0, description="Valor de peças/produtos")
    discount_amount: Decimal = Field(0.00, ge=0, description="Desconto")
    total_amount: Decimal = Field(0.00, ge=0, description="Valor total")
    
    # Garantia
    warranty_days: Optional[int] = Field(0, ge=0, description="Dias de garantia")

    # Pagamento
    payment_condition: Literal['a_vista', 'parcelado'] = Field('a_vista', description="Forma de pagamento")
    installment_count: Optional[int] = Field(1, ge=1, description="Numero de parcelas")
    down_payment: Optional[Decimal] = Field(0.00, ge=0, description="Valor de entrada")
    first_installment_date: Optional[date] = Field(None, description="Data da primeira parcela")
    payment_due_date: Optional[date] = Field(None, description="Vencimento para pagamento a vista")
    payment_description: Optional[str] = Field(None, description="Descricao do pagamento")
    payment_status: Literal['pending', 'partial', 'paid', 'canceled', 'pendente', 'parcial', 'pago', 'vencido'] = Field('pendente', description="Status do pagamento")
    payment_method: Optional[str] = Field(None, max_length=50, description="Método de pagamento")
    include_images_in_report: bool = Field(False, description="Incluir imagens no relatorio")

    total_services: Decimal = Field(0.00, ge=0)
    total_products: Decimal = Field(0.00, ge=0)
    total_displacement: Decimal = Field(0.00, ge=0)
    total_discount: Decimal = Field(0.00, ge=0)
    total_amount_enterprise: Decimal = Field(0.00, ge=0)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Assinaturas e anexos
    customer_signature: Optional[str] = Field(None, description="Assinatura do cliente em base64")
    customer_signature_name: Optional[str] = Field(None, max_length=200)
    customer_signature_date: Optional[datetime] = None
    technician_signature: Optional[str] = Field(None, description="Assinatura do técnico em base64")
    technician_signature_name: Optional[str] = Field(None, max_length=200)
    technician_signature_date: Optional[datetime] = None
    attachments_notes: Optional[str] = None
    
    # Itens relacionados (opcionais no create)
    items: Optional[List[ServiceOrderItemCreate]] = Field([], description="Itens de serviço")
    products: Optional[List[ServiceOrderProductCreate]] = Field([], description="Produtos utilizados")
    equipments: Optional[List[ServiceOrderEquipmentCreate]] = Field([], description="Equipamentos")
    installments: Optional[List[ServiceOrderInstallmentCreate]] = Field([], description="Parcelas")

    model_config = {"json_schema_extra": {
        "example": {
            "customer_id": "123e4567-e89b-12d3-a456-426614174000",
            "order_type": "comercial",
            "title": "Manutenção preventiva em motor elétrico",
            "description": "Revisão completa do motor trifásico 10CV",
            "requester": "João Silva",
            "problem_description": "Motor apresentando ruído anormal",
            "status": "pendente",
            "priority": "alta",
            "expected_date": "2025-12-31",
            "equipment": "Motor Elétrico WEG 10CV",
            "brand_model": "WEG W22 10CV",
            "serial_number": "WEG123456789",
            "total_amount": 600.00,
            "warranty_days": 90
        }
    }}


class ServiceOrderUpdate(BaseModel):
    """Schema para atualização parcial (PATCH)."""
    customer_id: Optional[UUID] = None
    order_type: Optional[Literal['comercial', 'operacional']] = None
    service_type: Optional[str] = Field(None, max_length=100)
    proposal_id: Optional[UUID] = None
    location: Optional[str] = Field(None, max_length=200)
    code: Optional[str] = Field(None, max_length=20)
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    technical_report: Optional[str] = None
    observations: Optional[str] = None
    client_name: Optional[str] = Field(None, max_length=200)
    client_document: Optional[str] = Field(None, max_length=30)
    client_phone: Optional[str] = Field(None, max_length=30)
    client_email: Optional[str] = Field(None, max_length=255)
    client_address: Optional[str] = None
    requester: Optional[str] = Field(None, max_length=200)
    problem_description: Optional[str] = None
    status: Optional[Literal['draft', 'open', 'in_progress', 'waiting_parts', 'completed', 'canceled', 'pendente', 'em_execucao', 'finalizada', 'cancelada']] = None
    priority: Optional[Literal['low', 'medium', 'high', 'urgent', 'baixa', 'normal', 'alta', 'urgente']] = None
    opening_date: Optional[date] = None
    expected_date: Optional[date] = None
    scheduled_date: Optional[date] = None
    start_date: Optional[datetime] = None
    completed_date: Optional[date] = None
    completion_date: Optional[datetime] = None
    technician: Optional[str] = Field(None, max_length=100)
    equipment: Optional[str] = Field(None, max_length=200)
    brand_model: Optional[str] = Field(None, max_length=200)
    serial_number: Optional[str] = Field(None, max_length=100)
    reported_defect: Optional[str] = None
    technical_diagnosis: Optional[str] = None
    solution: Optional[str] = None
    notes: Optional[str] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    total_hours: Optional[str] = Field(None, max_length=20)
    morning_entry_time: Optional[time] = None
    lunch_exit_time: Optional[time] = None
    lunch_return_time: Optional[time] = None
    evening_exit_time: Optional[time] = None
    overtime_entry_time: Optional[time] = None
    overtime_exit_time: Optional[time] = None
    regular_hours: Optional[Decimal] = Field(None, ge=0)
    overtime_hours: Optional[Decimal] = Field(None, ge=0)
    lunch_break_minutes: Optional[int] = Field(None, ge=0)
    initial_km: Optional[int] = Field(None, ge=0)
    final_km: Optional[int] = Field(None, ge=0)
    total_km: Optional[str] = Field(None, max_length=20)
    service_amount: Optional[Decimal] = Field(None, ge=0)
    parts_amount: Optional[Decimal] = Field(None, ge=0)
    discount_amount: Optional[Decimal] = Field(None, ge=0)
    total_amount: Optional[Decimal] = Field(None, ge=0)
    warranty_days: Optional[int] = Field(None, ge=0)
    payment_condition: Optional[Literal['a_vista', 'parcelado']] = None
    installment_count: Optional[int] = Field(None, ge=1)
    down_payment: Optional[Decimal] = Field(None, ge=0)
    first_installment_date: Optional[date] = None
    payment_due_date: Optional[date] = None
    payment_description: Optional[str] = None
    payment_status: Optional[Literal['pending', 'partial', 'paid', 'canceled', 'pendente', 'parcial', 'pago', 'vencido']] = None
    payment_method: Optional[str] = Field(None, max_length=50)
    include_images_in_report: Optional[bool] = None
    total_services: Optional[Decimal] = Field(None, ge=0)
    total_products: Optional[Decimal] = Field(None, ge=0)
    total_displacement: Optional[Decimal] = Field(None, ge=0)
    total_discount: Optional[Decimal] = Field(None, ge=0)
    total_amount_enterprise: Optional[Decimal] = Field(None, ge=0)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    customer_signature: Optional[str] = None
    customer_signature_name: Optional[str] = Field(None, max_length=200)
    customer_signature_date: Optional[datetime] = None
    technician_signature: Optional[str] = None
    technician_signature_name: Optional[str] = Field(None, max_length=200)
    technician_signature_date: Optional[datetime] = None
    attachments_notes: Optional[str] = None
    items: Optional[List[ServiceOrderItemUpsert]] = None
    products: Optional[List[ServiceOrderProductUpsert]] = None
    equipments: Optional[List[ServiceOrderEquipmentUpsert]] = None
    installments: Optional[List[ServiceOrderInstallmentUpsert]] = None


class ServiceOrderStatusChange(BaseModel):
    """Schema para alteração de status."""
    new_status: Literal['draft', 'open', 'in_progress', 'waiting_parts', 'completed', 'canceled', 'pendente', 'em_execucao', 'finalizada', 'cancelada']


class ServiceOrderOut(BaseModel):
    """Schema de saída de ordem de serviço (response)."""
    id: UUID
    number: str
    code: Optional[str]
    customer_id: Optional[UUID]
    customer_name: Optional[str] = None
    user_id: UUID
    order_type: str
    service_type: Optional[str]
    proposal_id: Optional[UUID]
    location: Optional[str]
    title: str
    description: Optional[str]
    technical_report: Optional[str]
    observations: Optional[str]
    client_name: Optional[str]
    client_document: Optional[str]
    client_phone: Optional[str]
    client_email: Optional[str]
    client_address: Optional[str]
    requester: Optional[str]
    problem_description: Optional[str]
    status: str
    priority: str
    opening_date: Optional[date]
    expected_date: Optional[date]
    scheduled_date: Optional[date]
    start_date: Optional[datetime]
    completed_date: Optional[date]
    completion_date: Optional[datetime]
    technician: Optional[str]
    equipment: Optional[str]
    brand_model: Optional[str]
    serial_number: Optional[str]
    reported_defect: Optional[str]
    technical_diagnosis: Optional[str]
    solution: Optional[str]
    notes: Optional[str]
    start_time: Optional[time]
    end_time: Optional[time]
    total_hours: Optional[str]
    morning_entry_time: Optional[time]
    lunch_exit_time: Optional[time]
    lunch_return_time: Optional[time]
    evening_exit_time: Optional[time]
    overtime_entry_time: Optional[time]
    overtime_exit_time: Optional[time]
    regular_hours: Optional[Decimal]
    overtime_hours: Optional[Decimal]
    lunch_break_minutes: Optional[int]
    initial_km: Optional[int]
    final_km: Optional[int]
    total_km: Optional[str]
    service_amount: Optional[Decimal]
    parts_amount: Optional[Decimal]
    discount_amount: Optional[Decimal]
    total_amount: Optional[Decimal]
    warranty_days: Optional[int]
    payment_condition: str
    installment_count: Optional[int]
    down_payment: Optional[Decimal]
    first_installment_date: Optional[date]
    payment_due_date: Optional[date]
    payment_description: Optional[str]
    payment_status: str
    payment_method: Optional[str]
    include_images_in_report: Optional[bool]
    total_services: Optional[Decimal]
    total_products: Optional[Decimal]
    total_displacement: Optional[Decimal]
    total_discount: Optional[Decimal]
    total_amount_enterprise: Optional[Decimal]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    customer_signature: Optional[str]
    customer_signature_name: Optional[str]
    customer_signature_date: Optional[datetime]
    technician_signature: Optional[str]
    technician_signature_name: Optional[str]
    technician_signature_date: Optional[datetime]
    attachments_notes: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    deleted_at: Optional[datetime]
    deleted_by: Optional[UUID]
    
    # Relações (opcionais - carregar apenas quando necessário)
    items: Optional[List[ServiceOrderItemOut]] = []
    products: Optional[List[ServiceOrderProductOut]] = []
    equipments: Optional[List[ServiceOrderEquipmentOut]] = []
    installments: Optional[List[ServiceOrderInstallmentOut]] = []
    attachments: Optional[List[ServiceOrderAttachmentOut]] = []

    model_config = {"from_attributes": True}


class ServiceOrderSummary(BaseModel):
    """Schema resumido para listagens."""
    id: UUID
    number: str
    customer_id: UUID
    customer_name: Optional[str] = None
    user_id: UUID
    title: str
    order_type: str
    service_type: Optional[str]
    status: str
    priority: str
    opening_date: Optional[date]
    expected_date: Optional[date]
    technician: Optional[str]
    equipment: Optional[str]
    total_amount: Decimal
    payment_condition: Optional[str] = None
    payment_status: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}
