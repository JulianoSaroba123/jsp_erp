"""
Routes FastAPI para Proposals (Propostas Comerciais).

Endpoints disponíveis:
- GET /proposals → Listar com paginação + filtros
- POST /proposals → Criar proposta
- GET /proposals/{id} → Buscar por ID
- GET /proposals/number/{number} → Buscar por número
- PATCH /proposals/{id} → Atualizar
- DELETE /proposals/{id} → Remover (soft delete)
- PATCH /proposals/{id}/status → Alterar status
- POST /proposals/{id}/convert-to-os → **CONVERSÃO PARA OS** (CRÍTICO)
- GET /proposals/{id}/items → Listar itens
- POST /proposals/{id}/items → Adicionar item
- GET /proposals/{id}/products → Listar produtos
- POST /proposals/{id}/products → Adicionar produto
"""

from typing import List, Optional
from uuid import UUID
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML
import os

from app.security.deps import get_current_user, get_db
from app.services.proposal_service import ProposalService
from app.models.user import User
from app.schemas.proposal_schema import (
    ProposalCreate,
    ProposalUpdate,
    ProposalOut,
    ProposalSummary,
    ProposalsResponse,
    ProposalItemCreate,
    ProposalItemOut,
    ProposalProductCreate,
    ProposalProductOut,
    ConvertProposalToOSRequest,
    ConvertProposalToOSResponse,
    GenerateShareLinkRequest,
    ShareLinkResponse
)
from app.schemas.service_order_schema import ServiceOrderOut
from app.exceptions.errors import ValidationError, NotFoundError


# ==================== CONFIGURAÇÕES DA EMPRESA ====================

def get_company_settings(db: Session = None) -> dict:
    """
    Retorna as configurações da empresa para uso nos templates.
    
    Prioridade:
    1. Busca do banco de dados (core.settings)
    2. Fallback para .env
    3. Fallback para valores padrão
    """
    from app.models.settings import Settings
    from uuid import UUID
    
    SETTINGS_ID = UUID("00000000-0000-0000-0000-000000000001")
    
    # Se db não for fornecido, criar uma sessão temporária
    if db is None:
        from app.database import SessionLocal
        db_session = SessionLocal()
        should_close = True
    else:
        db_session = db
        should_close = False
    
    try:
        # Tentar buscar do banco
        settings = db_session.query(Settings).filter(Settings.id == SETTINGS_ID).first()
        
        if settings:
            # Values já é um array no novo modelo
            values_list = settings.values if settings.values else []
            
            # Phones já é um array no novo modelo  
            phone = settings.phones[0] if settings.phones and len(settings.phones) > 0 else None
            phone_2 = settings.phones[1] if settings.phones and len(settings.phones) > 1 else None
            
            config = {
                "company_name": settings.company_name or "",
                "trade_name": settings.trade_name,
                "cnpj": settings.cnpj,
                "email": settings.email,
                "phone": phone,
                "phone_2": phone_2,
                "website": None,  # Campo removido do novo modelo
                "street": settings.street_address,
                "neighborhood": settings.neighborhood,
                "city": settings.city,
                "state": settings.state,
                "cep": settings.postal_code,
                "bank_name": settings.bank_name,
                "bank_agency": settings.bank_agency,
                "bank_account": settings.bank_account,
                "pix_key": settings.pix_key,
                "logo_url": settings.logo_url,
                "mission": settings.mission,
                "vision": settings.vision,
                "company_values": values_list,
                "pdf_header_text": settings.pdf_header_text,
                "pdf_footer_text": settings.pdf_footer_text,
                "default_proposal_message": settings.default_proposal_message,
            }
            return config
    except Exception as e:
        # Se houver erro ao buscar do banco, logar e continuar para fallback
        print(f"⚠️ Erro ao buscar settings do banco: {e}")
    finally:
        if should_close:
            db_session.close()
    
    # FALLBACK: Ler do .env
    values_string = os.getenv("COMPANY_VALUES", "Qualidade,Comprometimento,Inovação,Sustentabilidade,Ética")
    values_list = [v.strip() for v in values_string.split(",")]
    
    config = {
        "company_name": os.getenv("COMPANY_NAME", "JSP Automação Industrial & Solar"),
        "trade_name": os.getenv("COMPANY_TRADE_NAME", "JSP Elétrica"),
        "cnpj": os.getenv("COMPANY_CNPJ", "41.280.764/0001-65"),
        "email": os.getenv("COMPANY_EMAIL", "atendimento@eletricasaroba.com"),
        "phone": os.getenv("COMPANY_PHONE", "(54) 99191-7865"),
        "phone_2": os.getenv("COMPANY_PHONE_2", "(54) 98456-3049"),
        "website": os.getenv("COMPANY_WEBSITE", "www.eletricasaroba.com"),
        "street": os.getenv("COMPANY_STREET", "Rua dos Industriais, 1234"),
        "neighborhood": os.getenv("COMPANY_NEIGHBORHOOD", "Centro"),
        "city": os.getenv("COMPANY_CITY", "Passo Fundo"),
        "state": os.getenv("COMPANY_STATE", "RS"),
        "cep": os.getenv("COMPANY_CEP", "99010-000"),
        "bank_name": os.getenv("COMPANY_BANK_NAME", "CORA SCFI 403"),
        "bank_agency": os.getenv("COMPANY_BANK_AGENCY", "0001"),
        "bank_account": os.getenv("COMPANY_BANK_ACCOUNT", "4633457-0"),
        "pix_key": os.getenv("COMPANY_PIX_KEY", "atendimento@eletricasaroba.com"),
        "logo_url": os.getenv("COMPANY_LOGO_URL", None),
        "mission": os.getenv("COMPANY_MISSION", "Fornecer soluções completas em automação industrial e energia solar, agregando valor ao negócio dos nossos clientes."),
        "vision": os.getenv("COMPANY_VISION", "Ser referência em automação industrial e energia renovável no Rio Grande do Sul até 2027."),
        "company_values": values_list,
    }
    
    return config


router = APIRouter(
    prefix="/proposals",
    tags=["Proposals"]
)


# ==================== CRUD BÁSICO ====================

@router.get("", response_model=ProposalsResponse)
def list_proposals(
    page: int = Query(1, ge=1, description="Número da página"),
    page_size: int = Query(20, ge=1, le=100, description="Itens por página"),
    status: Optional[str] = Query(None, description="Filtrar por status"),
    customer_id: Optional[UUID] = Query(None, description="Filtrar por cliente"),
    search: Optional[str] = Query(None, description="Buscar por número ou título"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    **Lista propostas com paginação e filtros.**
    
    Filtros disponíveis:
    - status: rascunho, enviada, aprovada, rejeitada, cancelada
    - customer_id: UUID do cliente
    - search: busca em número (PROP2026001) ou título
    
    Requer autenticação JWT.
    """
    try:
        return ProposalService.list_proposals(
            db=db,
            page=page,
            page_size=page_size,
            status=status,
            customer_id=customer_id,
            search=search
        )
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("", response_model=ProposalOut, status_code=status.HTTP_201_CREATED)
def create_proposal(
    proposal_data: ProposalCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    **Cria nova proposta com itens e produtos.**
    
    Gera número automático (PROP2026001).
    Status inicial: 'rascunho' ou 'enviada'.
    
    Requer autenticação JWT.
    """
    try:
        proposal = ProposalService.create_proposal(
            db=db,
            proposal_data=proposal_data,
            user_id=current_user.id
        )
        return ProposalOut.model_validate(proposal)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{proposal_id}", response_model=ProposalOut)
def get_proposal(
    proposal_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    **Busca proposta por ID com relações.**
    
    Retorna cliente, itens e produtos eager-loaded.
    """
    try:
        proposal = ProposalService.get_proposal(db, proposal_id, with_relations=True)
        return ProposalOut.model_validate(proposal)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/number/{number}", response_model=ProposalOut)
def get_proposal_by_number(
    number: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    **Busca proposta por número (PROP2026001).**
    """
    try:
        proposal = ProposalService.get_proposal_by_number(db, number)
        return ProposalOut.model_validate(proposal)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch("/{proposal_id}", response_model=ProposalOut)
def update_proposal(
    proposal_id: UUID,
    update_data: ProposalUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    **Atualiza proposta.**
    
    Nota: Para alterar status, usar endpoint PATCH /proposals/{id}/status
    """
    try:
        proposal = ProposalService.update_proposal(db, proposal_id, update_data)
        return ProposalOut.model_validate(proposal)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{proposal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_proposal(
    proposal_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    **Remove proposta (soft delete).**
    
    Validação: Não pode deletar proposta aprovada que já gerou OS.
    """
    try:
        ProposalService.delete_proposal(db, proposal_id)
        return None
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ==================== GESTÃO DE STATUS ====================

@router.patch("/{proposal_id}/status", response_model=ProposalOut)
def change_proposal_status(
    proposal_id: UUID,
    new_status: str = Query(..., description="Novo status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    **Altera status da proposta.**
    
    Workflow válido:
    - rascunho → [enviada, cancelada]
    - enviada → [aprovada, rejeitada, cancelada]
    - aprovada → [cancelada] (apenas se não gerou OS)
    - rejeitada → [cancelada]
    - cancelada → não pode mudar
    """
    try:
        proposal = ProposalService.change_status(
            db=db,
            proposal_id=proposal_id,
            new_status=new_status,
            user_id=current_user.id
        )
        return ProposalOut.model_validate(proposal)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ==================== CONVERSÃO PARA OS (ENDPOINT CRÍTICO) ====================

@router.post("/{proposal_id}/convert-to-os", response_model=ConvertProposalToOSResponse)
def convert_proposal_to_service_order(
    proposal_id: UUID,
    request_data: ConvertProposalToOSRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    **🔥 CONVERSÃO: PROPOSTA APROVADA → ORDEM DE SERVIÇO**
    
    Esta é a função CENTRAL do fluxo de negócio.
    
    REGRAS DE NEGÓCIO:
    1. ✅ Apenas propostas 'aprovada' podem ser convertidas (status 400 se não aprovada)
    2. ✅ Uma proposta só pode gerar UMA OS (status 409 se já existe)
    3. ✅ A OS gerada tem tipo_ordem='projeto' e exibir_valores=False
    4. ✅ Copia cliente, valores, descrição, itens e produtos
    5. ✅ Vincula via proposta_id para rastreabilidade
    
    Body:
    - proposal_id: (já na URL)
    - technician_id: UUID (opcional)
    - expected_completion_date: date (opcional)
    - observations: string (opcional)
    
    Response:
    - success: true
    - message: "OS criada com sucesso"
    - service_order_id: UUID da OS criada
    - service_order_number: Número da OS (OS2026001)
    - proposal_number: Número da proposta (PROP2026001)
    
    Status Codes:
    - 200: Criada com sucesso
    - 400: Proposta não aprovada
    - 404: Proposta não encontrada
    - 409: Proposta já possui OS gerada (duplicidade)
    """
    try:
        # Converter proposta para OS
        service_order = ProposalService.convert_to_service_order(
            db=db,
            proposal_id=proposal_id,
            technician_id=request_data.technician_id,
            expected_completion_date=request_data.expected_completion_date,
            observations=request_data.observations
        )
        
        # Buscar proposta para pegar número
        proposal = ProposalService.get_proposal(db, proposal_id)
        
        # Retornar resposta estruturada
        return ConvertProposalToOSResponse(
            success=True,
            message=f"Ordem de Serviço {service_order.number} criada com sucesso a partir da proposta {proposal.number}",
            service_order_id=service_order.id,
            service_order_number=service_order.number,
            proposal_number=proposal.number
        )
    
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    
    except ValidationError as e:
        # Detectar tipo de erro por mensagem
        error_msg = str(e)
        
        # Erro 409: Proposta já possui OS (duplicidade)
        if "já possui uma ordem de serviço" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=error_msg
            )
        
        # Erro 400: Proposta não aprovada ou outros erros de validação
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )


# ==================== ITENS E PRODUTOS ====================

@router.get("/{proposal_id}/items", response_model=List[ProposalItemOut])
def list_proposal_items(
    proposal_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lista itens de uma proposta."""
    try:
        items = ProposalService.get_proposal_items(db, proposal_id)
        return [ProposalItemOut.model_validate(item) for item in items]
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{proposal_id}/items", response_model=ProposalItemOut, status_code=status.HTTP_201_CREATED)
def add_proposal_item(
    proposal_id: UUID,
    item_data: ProposalItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Adiciona item a uma proposta.
    
    Validação: Não pode adicionar em propostas aprovadas/rejeitadas.
    """
    try:
        item = ProposalService.add_proposal_item(
            db=db,
            proposal_id=proposal_id,
            item_data=item_data.model_dump()
        )
        return ProposalItemOut.model_validate(item)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{proposal_id}/products", response_model=List[ProposalProductOut])
def list_proposal_products(
    proposal_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lista produtos de uma proposta."""
    try:
        products = ProposalService.get_proposal_products(db, proposal_id)
        return [ProposalProductOut.model_validate(prod) for prod in products]
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{proposal_id}/products", response_model=ProposalProductOut, status_code=status.HTTP_201_CREATED)
def add_proposal_product(
    proposal_id: UUID,
    product_data: ProposalProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Adiciona produto a uma proposta.
    
    Validação: Não pode adicionar em propostas aprovadas/rejeitadas.
    """
    try:
        product = ProposalService.add_proposal_product(
            db=db,
            proposal_id=proposal_id,
            product_data=product_data.model_dump()
        )
        return ProposalProductOut.model_validate(product)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ==================== GERAÇÃO DE PDF ====================

@router.get("/{proposal_id}/pdf")
def generate_proposal_pdf(
    proposal_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    **Gera PDF da proposta comercial.**
    
    Retorna documento PDF formatado com:
    - Informações da proposta
    - Dados do cliente
    - Itens e produtos
    - Condições de pagamento
    - Parcelas (se parcelado)
    
    Requer autenticação JWT.
    """
    try:
        # Busca proposta com relações
        proposal = ProposalService.get_proposal(db, proposal_id, with_relations=True)
        
        # Busca configurações da empresa
        company = get_company_settings()
        
        # Configura Jinja2
        template_dir = Path(__file__).parent.parent / "templates"
        env = Environment(loader=FileSystemLoader(str(template_dir)))
        template = env.get_template("proposal_pdf.html")
        
        # Renderiza HTML
        html_content = template.render(
            proposal=proposal,
            company=company,
            now=datetime.now()
        )
        
        # Gera PDF
        pdf_bytes = HTML(string=html_content).write_pdf()
        
        # Retorna PDF
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"inline; filename=proposta_{proposal.number}.pdf"
            }
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao gerar PDF: {str(e)}"
        )


# ==================== COMPARTILHAMENTO PÚBLICO ====================

@router.post("/{proposal_id}/generate-share-link")
def generate_share_link(
    proposal_id: UUID,
    request: Optional[GenerateShareLinkRequest] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    **Gera link de compartilhamento público para PDF da proposta.**
    
    O link gerado permite acesso ao PDF sem autenticação.
    
    Args:
        proposal_id: ID da proposta
        request: Configurações do link (opcional)
            - expires_in_days: Dias até expiração (None = sem expiração)
    
    Returns:
        ShareLinkResponse com token e URL gerada
    
    Requer autenticação JWT.
    """
    try:
        from app.schemas.proposal_schema import GenerateShareLinkRequest, ShareLinkResponse
        
        expires_in_days = None
        if request:
            expires_in_days = request.expires_in_days
        
        # Gerar token
        proposal = ProposalService.generate_share_link(
            db=db,
            proposal_id=proposal_id,
            expires_in_days=expires_in_days
        )
        
        # Construir URL completa
        # TODO: Pegar base_url do config ou request
        base_url = "http://localhost:8000"
        share_url = f"{base_url}/proposals/{proposal_id}/share/pdf?token={proposal.share_token}"
        
        return ShareLinkResponse(
            share_token=proposal.share_token,
            share_url=share_url,
            share_enabled=proposal.share_enabled,
            share_expires_at=proposal.share_expires_at,
            share_created_at=proposal.share_created_at
        )
        
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{proposal_id}/revoke-share-link")
def revoke_share_link(
    proposal_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    **Revoga link de compartilhamento de uma proposta.**
    
    O link deixa de funcionar imediatamente.
    
    Requer autenticação JWT.
    """
    try:
        ProposalService.revoke_share_link(db=db, proposal_id=proposal_id)
        return {"message": "Link de compartilhamento revogado com sucesso"}
        
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/{proposal_id}/share/pdf")
def get_shared_proposal_pdf(
    proposal_id: UUID,
    token: str,
    db: Session = Depends(get_db)
):
    """
    **Acesso público ao PDF da proposta via token de compartilhamento.**
    
    Este endpoint NÃO requer autenticação JWT.
    Qualquer pessoa com o token pode acessar o PDF.
    
    Args:
        proposal_id: ID da proposta
        token: Token de compartilhamento
    
    Returns:
        PDF da proposta
    
    Raises:
        400: Token inválido ou expirado
        404: Proposta não encontrada
    """
    try:
        # Validar token e obter proposta
        proposal = ProposalService.validate_share_token(
            db=db,
            proposal_id=proposal_id,
            token=token
        )
        
        # Busca configurações da empresa
        company = get_company_settings()
        
        # Configurar Jinja2
        template_dir = Path(__file__).parent.parent / "templates"
        env = Environment(loader=FileSystemLoader(str(template_dir)))
        template = env.get_template("proposal_pdf.html")
        
        # Renderizar HTML
        html_content = template.render(
            proposal=proposal,
            company=company,
            now=datetime.now()
        )
        
        # Gera PDF
        pdf_bytes = HTML(string=html_content).write_pdf()
        
        # Retorna PDF
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"inline; filename=proposta_{proposal.number}.pdf"
            }
        )
        
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao gerar PDF: {str(e)}"
        )

