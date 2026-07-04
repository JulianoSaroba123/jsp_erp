"""
Router de Service Orders - endpoints HTTP.
Responsabilidade: receber requests e chamar ServiceOrderService.
"""

from typing import List, Optional
from uuid import UUID
from uuid import uuid4

from fastapi import APIRouter, Body, Depends, HTTPException, Request, status, Query
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.services.service_order_service import (
    ServiceOrderService,
    ServiceOrderItemService,
    ServiceOrderProductService,
    ServiceOrderInstallmentService,
    ServiceOrderAttachmentService
)
from app.schemas.service_order_schema import (
    ServiceOrderCreate,
    ServiceOrderOut,
    ServiceOrderUpdate,
    ServiceOrderStatusChange,
    ServiceOrderSummary,
    ServiceOrderItemCreate,
    ServiceOrderItemOut,
    ServiceOrderProductCreate,
    ServiceOrderProductOut,
    ServiceOrderInstallmentCreate,
    ServiceOrderInstallmentOut,
    ServiceOrderInstallmentUpdate,
    ServiceOrderEquipmentCreate,
    ServiceOrderEquipmentOut,
    ServiceOrderAttachmentCreate,
    ServiceOrderAttachmentOut
)
from app.security.deps import get_current_user, get_db
from app.models.user import User
from app.exceptions.errors import ConflictError, NotFoundError, ValidationError
from app.services.audit_log_service import AuditLogService


router = APIRouter(prefix="/service-orders", tags=["Service Orders"])


@router.get("", status_code=status.HTTP_200_OK)
def list_service_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    order_status: Optional[str] = Query(None, alias="status"),
    priority: Optional[str] = Query(None),
    customer_id: Optional[UUID] = Query(None),
    search: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Lista ordens de serviço com paginação e filtros.
    
    **Autenticação obrigatória (Bearer token)**
    
    Query params:
    - page: número da página (default 1, min 1)
    - page_size: itens por página (default 20, max 100)
    - status: filtro por status (pendente, em_execucao, finalizada, cancelada)
    - priority: filtro por prioridade (baixa, normal, alta, urgente)
    - customer_id: filtro por cliente
    - search: busca em número, título, equipamento, técnico
    
    Response:
    {
      "items": [...],
      "page": 1,
      "page_size": 20,
      "total": 123
    }
    """
    try:
        user_id_filter = None if current_user.role == "admin" else current_user.id

        result = ServiceOrderService.list_service_orders(
            db=db,
            page=page,
            page_size=page_size,
            user_id=user_id_filter,
            status=order_status,
            priority=priority,
            customer_id=customer_id,
            search=search
        )
        
        # Usa ServiceOrderSummary para listagem (sem relações)
        items_out = [ServiceOrderSummary.model_validate(so) for so in result["items"]]
        
        return {
            "items": items_out,
            "page": result["page"],
            "page_size": result["page_size"],
            "total": result["total"]
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao listar ordens de serviço: {str(e)}"
        )


@router.post("", status_code=status.HTTP_201_CREATED, response_model=ServiceOrderOut)
def create_service_order(
    request: Request,
    service_order_data: ServiceOrderCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Cria nova ordem de serviço.
    
    **Autenticação obrigatória (Bearer token)**
    
    Body (ServiceOrderCreate):
    - customer_id: ID do cliente (obrigatório)
    - title: título (obrigatório)
    - description: descrição detalhada
    - status: status inicial (default: pendente)
    - priority: prioridade (default: normal)
    - equipment, technician, etc.
    - items: lista de serviços realizados (opcional)
    - products: lista de produtos utilizados (opcional)
    - installments: lista de parcelas (opcional)
    
    Número da OS é gerado automaticamente (formato: OS2025001, OS2025002...).
    """
    try:
        # Converte Pydantic model para dict
        so_dict = service_order_data.model_dump(exclude_unset=True)
        
        # Adiciona user_id do usuário autenticado
        so_dict['user_id'] = current_user.id
        
        # Cria ordem de serviço
        service_order = ServiceOrderService.create_service_order(
            db=db,
            service_order_data=so_dict
        )
        
        # Recarrega com relações para retorno completo
        service_order = ServiceOrderService.get_service_order(
            db=db,
            service_order_id=service_order.id,
            with_relations=True
        )
        
        response = ServiceOrderOut.model_validate(service_order)
        request_id = request.headers.get("X-Request-ID", str(uuid4()))
        AuditLogService.log_action(
            db=db,
            user_id=current_user.id,
            action="create",
            entity_type="service_order",
            entity_id=service_order.id,
            request_id=request_id,
            before=None,
            after=response.model_dump(mode="json"),
        )
        return response
    
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao criar ordem de serviço: {str(e)}"
        )


@router.get("/{service_order_id}", status_code=status.HTTP_200_OK, response_model=ServiceOrderOut)
def get_service_order(
    service_order_id: UUID,
    with_relations: bool = Query(True),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Busca ordem de serviço por ID.
    
    **Autenticação obrigatória (Bearer token)**
    
    Query params:
    - with_relations: se True, inclui itens, produtos, parcelas e anexos (default: True)
    """
    try:
        user_id_filter = None if current_user.role == "admin" else current_user.id
        service_order = ServiceOrderService.get_service_order_scoped(
            db=db,
            service_order_id=service_order_id,
            user_id=user_id_filter,
            with_relations=with_relations
        )
        
        if not service_order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Ordem de serviço {service_order_id} não encontrada"
            )
        
        return ServiceOrderOut.model_validate(service_order)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao buscar ordem de serviço: {str(e)}"
        )


@router.get("/number/{number}", status_code=status.HTTP_200_OK, response_model=ServiceOrderOut)
def get_service_order_by_number(
    number: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Busca ordem de serviço por número (OS2025001, etc).
    
    **Autenticação obrigatória (Bearer token)**
    """
    try:
        service_order = ServiceOrderService.get_service_order_by_number(db=db, number=number)
        
        if not service_order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Ordem de serviço {number} não encontrada"
            )
        
        if current_user.role != "admin" and service_order.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Ordem de serviço {number} não encontrada"
            )

        return ServiceOrderOut.model_validate(service_order)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao buscar ordem de serviço: {str(e)}"
        )


@router.patch("/{service_order_id}", status_code=status.HTTP_200_OK, response_model=ServiceOrderOut)
def update_service_order(
    request: Request,
    service_order_id: UUID,
    service_order_data: ServiceOrderUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Atualiza ordem de serviço existente (PATCH).
    
    **Autenticação obrigatória (Bearer token)**
    
    Todos os campos do body são opcionais.
    Apenas os campos fornecidos serão atualizados.
    """
    try:
        scoped_order = ServiceOrderService.get_service_order_scoped(
            db=db,
            service_order_id=service_order_id,
            user_id=None if current_user.role == "admin" else current_user.id,
            with_relations=False,
        )
        if not scoped_order:
            raise NotFoundError("Ordem de serviço não encontrada")

        # Atualização parcial preservando campos ausentes.
        update_dict = service_order_data.model_dump(exclude_unset=True)
        
        if not update_dict:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Nenhum campo fornecido para atualização"
            )
        
        service_order = ServiceOrderService.update_service_order(
            db=db,
            service_order_id=service_order_id,
            update_data=update_dict
        )
        
        # Recarrega com relações
        service_order = ServiceOrderService.get_service_order(
            db=db,
            service_order_id=service_order.id,
            with_relations=True
        )
        
        response = ServiceOrderOut.model_validate(service_order)
        request_id = request.headers.get("X-Request-ID", str(uuid4()))
        AuditLogService.log_action(
            db=db,
            user_id=current_user.id,
            action="update",
            entity_type="service_order",
            entity_id=service_order.id,
            request_id=request_id,
            before=None,
            after=response.model_dump(mode="json"),
        )
        return response
    
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except ConflictError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao atualizar ordem de serviço: {str(e)}"
        )


@router.delete("/{service_order_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_service_order(
    request: Request,
    service_order_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Remove ordem de serviço (soft delete).
    
    **Autenticação obrigatória (Bearer token)**
    **Permissão necessária: admin**
    
    Remove também todos os registros relacionados (cascade).
    """
    try:
        scoped_order = ServiceOrderService.get_service_order_scoped(
            db=db,
            service_order_id=service_order_id,
            user_id=None if current_user.role == "admin" else current_user.id,
            with_relations=False,
        )
        if not scoped_order:
            raise NotFoundError("Ordem de serviço não encontrada")

        ServiceOrderService.delete_service_order(db=db, service_order_id=service_order_id)

        request_id = request.headers.get("X-Request-ID", str(uuid4()))
        AuditLogService.log_action(
            db=db,
            user_id=current_user.id,
            action="delete",
            entity_type="service_order",
            entity_id=service_order_id,
            request_id=request_id,
            before=None,
            after=None,
        )
        return None
    
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ConflictError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao remover ordem de serviço: {str(e)}"
        )


@router.patch("/{service_order_id}/status", status_code=status.HTTP_200_OK, response_model=ServiceOrderOut)
def change_status(
    service_order_id: UUID,
    status_data: Optional[ServiceOrderStatusChange] = Body(None),
    new_status: Optional[str] = Query(None, pattern="^(draft|open|in_progress|waiting_parts|completed|canceled|pendente|em_execucao|finalizada|cancelada)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Altera status da ordem de serviço.
    
    **Autenticação obrigatória (Bearer token)**
    
    Status válidos: pendente, em_execucao, finalizada, cancelada
    
    Lógica automática:
    - pendente -> em_execucao: define start_date
    - em_execucao -> finalizada: define completion_date
    """
    try:
        status_value = status_data.new_status if status_data else new_status
        if not status_value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Informe new_status no corpo da requisição ou na query string"
            )

        scoped_order = ServiceOrderService.get_service_order_scoped(
            db=db,
            service_order_id=service_order_id,
            user_id=None if current_user.role == "admin" else current_user.id,
            with_relations=False,
        )
        if not scoped_order:
            raise NotFoundError("Ordem de serviço não encontrada")

        service_order = ServiceOrderService.change_status(
            db=db,
            service_order_id=service_order_id,
            new_status=status_value
        )
        
        # Recarrega com relações
        service_order = ServiceOrderService.get_service_order(
            db=db,
            service_order_id=service_order.id,
            with_relations=True
        )
        
        return ServiceOrderOut.model_validate(service_order)
    
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except ConflictError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao alterar status: {str(e)}"
        )


@router.get("/{service_order_id}/print", response_class=HTMLResponse, status_code=status.HTTP_200_OK)
def print_service_order(
        service_order_id: UUID,
        version: str = Query("summary", pattern="^(summary|technical)$"),
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
):
        """Renderização HTML pronta para impressão profissional da OS."""
        scoped_order = ServiceOrderService.get_service_order_scoped(
                db=db,
                service_order_id=service_order_id,
                user_id=None if current_user.role == "admin" else current_user.id,
                with_relations=True,
        )
        if not scoped_order:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ordem de serviço não encontrada")

        products_rows = "".join(
                f"<tr><td>{p.description}</td><td>{p.quantity}</td><td>{p.unit_price}</td><td>{p.total_price}</td></tr>"
                for p in (scoped_order.products or [])
        )
        items_rows = "".join(
                f"<tr><td>{i.description}</td><td>{i.quantity}</td><td>{i.unit_price}</td><td>{i.total_price}</td></tr>"
                for i in (scoped_order.items or [])
        )
        installments_rows = "".join(
                f"<tr><td>{ins.installment_number}</td><td>{ins.due_date}</td><td>{ins.amount}</td><td>{ins.status}</td></tr>"
                for ins in (scoped_order.installments or [])
        )
        equipments_rows = "".join(
                f"<tr><td>{eq.equipment_name}</td><td>{eq.brand or ''}</td><td>{eq.model or ''}</td><td>{eq.serial_number or ''}</td></tr>"
                for eq in (scoped_order.equipments or [])
        )

        technical_block = ""
        if version == "technical":
                technical_block = f"""
                <section>
                    <h3>Diagnóstico técnico</h3>
                    <p>{scoped_order.technical_diagnosis or scoped_order.technical_report or '-'}</p>
                    <h3>Observações técnicas</h3>
                    <p>{scoped_order.observations or scoped_order.notes or '-'}</p>
                </section>
                """

        html = f"""
        <!DOCTYPE html>
        <html lang=\"pt-BR\">
        <head>
            <meta charset=\"UTF-8\" />
            <title>Impressão OS {scoped_order.number}</title>
            <style>
                body {{ font-family: 'Segoe UI', sans-serif; margin: 24px; color: #0f172a; }}
                .header {{ display:flex; justify-content:space-between; border-bottom:2px solid #1e293b; margin-bottom:16px; padding-bottom:8px; }}
                .logo {{ font-weight:700; font-size:20px; }}
                .grid {{ display:grid; grid-template-columns: 1fr 1fr; gap:12px; margin-bottom:12px; }}
                table {{ width:100%; border-collapse:collapse; margin:10px 0; }}
                th,td {{ border:1px solid #cbd5e1; padding:6px; text-align:left; font-size:12px; }}
                th {{ background:#e2e8f0; }}
                .signatures {{ margin-top:32px; display:grid; grid-template-columns:1fr 1fr; gap:20px; }}
                .line {{ border-top:1px solid #334155; margin-top:30px; padding-top:6px; font-size:12px; }}
                @media print {{ .print-btn {{ display:none; }} }}
            </style>
        </head>
        <body>
            <button class=\"print-btn\" onclick=\"window.print()\">Imprimir</button>
            <div class=\"header\"><div class=\"logo\">JSP ERP</div><div>OS {scoped_order.number}</div></div>
            <div class=\"grid\">
                <div><strong>Cliente:</strong> {scoped_order.client_name or scoped_order.customer_name or '-'}</div>
                <div><strong>Documento:</strong> {scoped_order.client_document or '-'}</div>
                <div><strong>Telefone:</strong> {scoped_order.client_phone or '-'}</div>
                <div><strong>E-mail:</strong> {scoped_order.client_email or '-'}</div>
            </div>
            <div><strong>Endereço:</strong> {scoped_order.client_address or '-'}</div>

            <h3>Equipamentos</h3>
            <table><thead><tr><th>Equipamento</th><th>Marca</th><th>Modelo</th><th>Série</th></tr></thead><tbody>{equipments_rows or '<tr><td colspan="4">Sem registros</td></tr>'}</tbody></table>

            <h3>Serviços executados</h3>
            <table><thead><tr><th>Descrição</th><th>Qtd</th><th>Unitário</th><th>Total</th></tr></thead><tbody>{items_rows or '<tr><td colspan="4">Sem registros</td></tr>'}</tbody></table>

            <h3>Produtos</h3>
            <table><thead><tr><th>Descrição</th><th>Qtd</th><th>Unitário</th><th>Total</th></tr></thead><tbody>{products_rows or '<tr><td colspan="4">Sem registros</td></tr>'}</tbody></table>

            <h3>Parcelas</h3>
            <table><thead><tr><th>Parcela</th><th>Vencimento</th><th>Valor</th><th>Status</th></tr></thead><tbody>{installments_rows or '<tr><td colspan="4">Sem registros</td></tr>'}</tbody></table>

            <h3>Total geral: {scoped_order.total_amount}</h3>
            {technical_block}
            <div class=\"signatures\">
                <div class=\"line\">Assinatura do Cliente</div>
                <div class=\"line\">Assinatura do Técnico</div>
            </div>
        </body>
        </html>
        """
        return HTMLResponse(content=html)


@router.get("/statistics/dashboard", status_code=status.HTTP_200_OK)
def get_statistics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retorna estatísticas para dashboard.
    
    **Autenticação obrigatória (Bearer token)**
    
    Response:
    {
      "total": 150,
      "pendente": 20,
      "em_execucao": 15,
      "finalizada_mes": 45
    }
    """
    try:
        stats = ServiceOrderService.get_statistics(db=db)
        return stats
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao buscar estatísticas: {str(e)}"
        )


# ==================== Rotas para Itens de Serviço ====================

@router.post("/{service_order_id}/items", status_code=status.HTTP_201_CREATED, response_model=ServiceOrderItemOut)
def add_item(
    service_order_id: UUID,
    item_data: ServiceOrderItemCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Adiciona item de serviço à ordem."""
    try:
        scoped_order = ServiceOrderService.get_service_order_scoped(
            db=db,
            service_order_id=service_order_id,
            user_id=None if current_user.role == "admin" else current_user.id,
        )
        if not scoped_order:
            raise NotFoundError("Ordem de serviço não encontrada")

        item_dict = item_data.model_dump()
        item = ServiceOrderItemService.add_item(db=db, service_order_id=service_order_id, item_data=item_dict)
        return ServiceOrderItemOut.model_validate(item)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{service_order_id}/items", status_code=status.HTTP_200_OK, response_model=List[ServiceOrderItemOut])
def list_items(
    service_order_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lista itens de serviço da ordem."""
    try:
        scoped_order = ServiceOrderService.get_service_order_scoped(
            db=db,
            service_order_id=service_order_id,
            user_id=None if current_user.role == "admin" else current_user.id,
        )
        if not scoped_order:
            raise NotFoundError("Ordem de serviço não encontrada")

        items = ServiceOrderItemService.list_items(db=db, service_order_id=service_order_id)
        return [ServiceOrderItemOut.model_validate(item) for item in items]
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# ==================== Rotas para Produtos ====================

@router.post("/{service_order_id}/products", status_code=status.HTTP_201_CREATED, response_model=ServiceOrderProductOut)
def add_product(
    service_order_id: UUID,
    product_data: ServiceOrderProductCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Adiciona produto utilizado à ordem."""
    try:
        scoped_order = ServiceOrderService.get_service_order_scoped(
            db=db,
            service_order_id=service_order_id,
            user_id=None if current_user.role == "admin" else current_user.id,
        )
        if not scoped_order:
            raise NotFoundError("Ordem de serviço não encontrada")

        product_dict = product_data.model_dump()
        product = ServiceOrderProductService.add_product(db=db, service_order_id=service_order_id, product_data=product_dict)
        return ServiceOrderProductOut.model_validate(product)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{service_order_id}/products", status_code=status.HTTP_200_OK, response_model=List[ServiceOrderProductOut])
def list_products(
    service_order_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lista produtos utilizados na ordem."""
    try:
        scoped_order = ServiceOrderService.get_service_order_scoped(
            db=db,
            service_order_id=service_order_id,
            user_id=None if current_user.role == "admin" else current_user.id,
        )
        if not scoped_order:
            raise NotFoundError("Ordem de serviço não encontrada")

        products = ServiceOrderProductService.list_products(db=db, service_order_id=service_order_id)
        return [ServiceOrderProductOut.model_validate(p) for p in products]
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# ==================== Rotas para Parcelas ====================

@router.post("/{service_order_id}/installments", status_code=status.HTTP_201_CREATED, response_model=ServiceOrderInstallmentOut)
def add_installment(
    service_order_id: UUID,
    installment_data: ServiceOrderInstallmentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Adiciona parcela à ordem."""
    try:
        installment_dict = installment_data.model_dump()
        installment = ServiceOrderInstallmentService.add_installment(
            db=db,
            service_order_id=service_order_id,
            installment_data=installment_dict
        )
        return ServiceOrderInstallmentOut.model_validate(installment)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{service_order_id}/installments", status_code=status.HTTP_200_OK, response_model=List[ServiceOrderInstallmentOut])
def list_installments(
    service_order_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lista parcelas da ordem."""
    try:
        installments = ServiceOrderInstallmentService.list_installments(db=db, service_order_id=service_order_id)
        return [ServiceOrderInstallmentOut.model_validate(i) for i in installments]
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.patch("/installments/{installment_id}/paid", status_code=status.HTTP_200_OK, response_model=ServiceOrderInstallmentOut)
def mark_installment_paid(
    installment_id: UUID,
    payment_date: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Marca uma parcela da OS como paga."""
    try:
        installment = ServiceOrderInstallmentService.mark_paid(
            db=db,
            installment_id=installment_id,
            payment_date=payment_date
        )
        return ServiceOrderInstallmentOut.model_validate(installment)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.patch("/installments/{installment_id}", status_code=status.HTTP_200_OK, response_model=ServiceOrderInstallmentOut)
def update_installment(
    installment_id: UUID,
    installment_data: ServiceOrderInstallmentUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Atualiza uma parcela da OS."""
    try:
        installment = ServiceOrderInstallmentService.update_installment(
            db=db,
            installment_id=installment_id,
            update_data=installment_data.model_dump(exclude_unset=True, exclude_none=True)
        )
        return ServiceOrderInstallmentOut.model_validate(installment)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete("/installments/{installment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_installment(
    installment_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove uma parcela da OS."""
    try:
        ServiceOrderInstallmentService.delete_installment(db=db, installment_id=installment_id)
        return None
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# ==================== Rotas para Anexos ====================

@router.post("/{service_order_id}/attachments", status_code=status.HTTP_201_CREATED, response_model=ServiceOrderAttachmentOut)
def add_attachment(
    service_order_id: UUID,
    attachment_data: ServiceOrderAttachmentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Registra metadados de anexo da ordem."""
    try:
        attachment = ServiceOrderAttachmentService.add_attachment(
            db=db,
            service_order_id=service_order_id,
            attachment_data=attachment_data.model_dump()
        )
        return ServiceOrderAttachmentOut.model_validate(attachment)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{service_order_id}/attachments", status_code=status.HTTP_200_OK, response_model=List[ServiceOrderAttachmentOut])
def list_attachments(
    service_order_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lista anexos registrados na ordem."""
    try:
        attachments = ServiceOrderAttachmentService.list_attachments(db=db, service_order_id=service_order_id)
        return [ServiceOrderAttachmentOut.model_validate(a) for a in attachments]
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete("/attachments/{attachment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_attachment(
    attachment_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove anexo da ordem."""
    try:
        ServiceOrderAttachmentService.delete_attachment(db=db, attachment_id=attachment_id)
        return None
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
