"""
Settings Routes - Endpoints para configurações do sistema
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import text
from uuid import UUID
import os

from app.security.deps import get_db, get_current_user
from app.models.settings import Settings
from app.schemas.settings_schema import SettingsResponse, SettingsUpdate
from app.models.user import User

router = APIRouter(tags=["settings"], prefix="/settings")

# ID fixo para garantir single-row
SETTINGS_ID = UUID("00000000-0000-0000-0000-000000000001")


def get_or_create_settings(db: Session) -> Settings:
    """
    Busca ou cria o registro único de settings.
    Se não existir, cria com dados do .env como fallback.
    """
    settings = db.query(Settings).filter(Settings.id == SETTINGS_ID).first()
    
    if not settings:
        # Criar settings com dados do .env
        phones = []
        if os.getenv("COMPANY_PHONE"):
            phones.append(os.getenv("COMPANY_PHONE"))
        if os.getenv("COMPANY_PHONE_2"):
            phones.append(os.getenv("COMPANY_PHONE_2"))
        
        values_str = os.getenv("COMPANY_VALUES", "")
        values_list = [v.strip() for v in values_str.split(",")] if values_str else []
        
        settings = Settings(
            id=SETTINGS_ID,
            company_name=os.getenv("COMPANY_NAME", ""),
            trade_name=os.getenv("COMPANY_TRADE_NAME"),
            cnpj=os.getenv("COMPANY_CNPJ"),
            email=os.getenv("COMPANY_EMAIL"),
            phones=phones if phones else None,
            street_address=os.getenv("COMPANY_STREET"),
            neighborhood=os.getenv("COMPANY_NEIGHBORHOOD"),
            city=os.getenv("COMPANY_CITY"),
            state=os.getenv("COMPANY_STATE"),
            postal_code=os.getenv("COMPANY_CEP"),
            logo_url=os.getenv("COMPANY_LOGO_URL"),
            bank_name=os.getenv("COMPANY_BANK_NAME"),
            bank_code=os.getenv("COMPANY_BANK_CODE"),
            bank_agency=os.getenv("COMPANY_BANK_AGENCY"),
            bank_account=os.getenv("COMPANY_BANK_ACCOUNT"),
            pix_key=os.getenv("COMPANY_PIX_KEY"),
            mission=os.getenv("COMPANY_MISSION"),
            vision=os.getenv("COMPANY_VISION"),
            values=values_list if values_list else None,
        )
        db.add(settings)
        db.commit()
        db.refresh(settings)
    
    return settings


@router.get("")
def get_settings(
    db: Session = Depends(get_db)
):
    """
    Retorna as configurações do sistema.
    PÚBLICO - Não exige autenticação (usado na página de login).
    """
    try:
        # Query SQL direta para evitar problemas de ORM
        result = db.execute(text("SELECT * FROM public.settings LIMIT 1"))
        row = result.fetchone()
        
        if not row:
            return {"error": "Settings not found"}
        
        # Retornar como dict - usando getattr para todos os campos para segurança
        return {
            "id": str(row.id) if hasattr(row, 'id') else None,
            "company_name": getattr(row, 'company_name', None),
            "trade_name": getattr(row, 'trade_name', None),
            "cnpj": getattr(row, 'cnpj', None),
            "email": getattr(row, 'email', None),
            "phones": getattr(row, 'phones', None),
            "street_address": getattr(row, 'street_address', None),
            "neighborhood": getattr(row, 'neighborhood', None),
            "city": getattr(row, 'city', None),
            "state": getattr(row, 'state', None),
            "postal_code": getattr(row, 'postal_code', None),
            "country": getattr(row, 'country', None),
            "latitude": float(row.latitude) if getattr(row, 'latitude', None) else None,
            "longitude": float(row.longitude) if getattr(row, 'longitude', None) else None,
            "logo_url": getattr(row, 'logo_url', None),
            "bank_name": getattr(row, 'bank_name', None),
            "bank_code": getattr(row, 'bank_code', None),
            "bank_agency": getattr(row, 'bank_agency', None),
            "bank_account": getattr(row, 'bank_account', None),
            "pix_key": getattr(row, 'pix_key', None),
            "mission": getattr(row, 'mission', None),
            "vision": getattr(row, 'vision', None),
            "values": getattr(row, 'values', None),
            "theme_primary_color": getattr(row, 'theme_primary_color', None),
            "theme_secondary_color": getattr(row, 'theme_secondary_color', None),
            "timezone": getattr(row, 'timezone', None),
            "language": getattr(row, 'language', None),
            "currency": getattr(row, 'currency', None),
            "date_format": getattr(row, 'date_format', None),
            "decimal_separator": getattr(row, 'decimal_separator', None),
            "thousand_separator": getattr(row, 'thousand_separator', None),
            "pdf_logo_position": getattr(row, 'pdf_logo_position', None),
            "pdf_logo_width": getattr(row, 'pdf_logo_width', None),
            "pdf_show_watermark": getattr(row, 'pdf_show_watermark', None),
            "pdf_header_text": getattr(row, 'pdf_header_text', None),
            "pdf_footer_text": getattr(row, 'pdf_footer_text', None),
            "default_proposal_message": getattr(row, 'default_proposal_message', None),
            "created_at": row.created_at.isoformat() if getattr(row, 'created_at', None) else None,
            "updated_at": row.updated_at.isoformat() if getattr(row, 'updated_at', None) else None,
        }
    except Exception as e:
        print(f"❌ ERRO em get_settings: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro ao buscar configurações: {str(e)}")


@router.put("", response_model=SettingsResponse)
def update_settings(
    data: SettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Atualiza as configurações do sistema.
    Apenas campos enviados são atualizados.
    """
    # Construir query UPDATE dinamicamente apenas com campos fornecidos
    update_data = data.model_dump(exclude_unset=True)
    
    if not update_data:
        raise HTTPException(status_code=400, detail="Nenhum campo para atualizar")
    
    # Construir SET clause
    set_clauses = []
    params = {"id": str(SETTINGS_ID)}
    
    for field, value in update_data.items():
        set_clauses.append(f"{field} = :{field}")
        params[field] = value
    
    # Adicionar updated_at
    set_clauses.append("updated_at = now()")
    
    query = f"UPDATE public.settings SET {', '.join(set_clauses)} WHERE id = :id"
    
    db.execute(text(query), params)
    db.commit()
    
    # Buscar settings atualizado com SQL
    result = db.execute(text("SELECT * FROM public.settings WHERE id = :id"), {"id": str(SETTINGS_ID)})
    row = result.fetchone()
    
    if not row:
        raise HTTPException(status_code=404, detail="Settings not found after update")
    
    # Converter row para dict (mesmo formato do GET)
    return {
        "id": str(row.id) if hasattr(row, 'id') else None,
        "company_name": getattr(row, 'company_name', None),
        "trade_name": getattr(row, 'trade_name', None),
        "cnpj": getattr(row, 'cnpj', None),
        "email": getattr(row, 'email', None),
        "phones": getattr(row, 'phones', None),
        "street_address": getattr(row, 'street_address', None),
        "neighborhood": getattr(row, 'neighborhood', None),
        "city": getattr(row, 'city', None),
        "state": getattr(row, 'state', None),
        "postal_code": getattr(row, 'postal_code', None),
        "country": getattr(row, 'country', None),
        "latitude": float(row.latitude) if getattr(row, 'latitude', None) else None,
        "longitude": float(row.longitude) if getattr(row, 'longitude', None) else None,
        "logo_url": getattr(row, 'logo_url', None),
        "bank_name": getattr(row, 'bank_name', None),
        "bank_code": getattr(row, 'bank_code', None),
        "bank_agency": getattr(row, 'bank_agency', None),
        "bank_account": getattr(row, 'bank_account', None),
        "pix_key": getattr(row, 'pix_key', None),
        "mission": getattr(row, 'mission', None),
        "vision": getattr(row, 'vision', None),
        "values": getattr(row, 'values', None),
        "theme_primary_color": getattr(row, 'theme_primary_color', None),
        "theme_secondary_color": getattr(row, 'theme_secondary_color', None),
        "timezone": getattr(row, 'timezone', None),
        "language": getattr(row, 'language', None),
        "currency": getattr(row, 'currency', None),
        "date_format": getattr(row, 'date_format', None),
        "decimal_separator": getattr(row, 'decimal_separator', None),
        "thousand_separator": getattr(row, 'thousand_separator', None),
        "pdf_logo_position": getattr(row, 'pdf_logo_position', None),
        "pdf_logo_width": getattr(row, 'pdf_logo_width', None),
        "pdf_show_watermark": getattr(row, 'pdf_show_watermark', None),
        "pdf_header_text": getattr(row, 'pdf_header_text', None),
        "pdf_footer_text": getattr(row, 'pdf_footer_text', None),
        "default_proposal_message": getattr(row, 'default_proposal_message', None),
        "created_at": row.created_at.isoformat() if getattr(row, 'created_at', None) else None,
        "updated_at": row.updated_at.isoformat() if getattr(row, 'updated_at', None) else None,
    }


@router.post("/logo")
async def upload_logo(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Upload de logo da empresa.
    Aceita arquivos PNG, JPG, JPEG ou SVG (máximo 5MB).
    Converte para base64 e salva no banco.
    """
    import base64
    
    # Validar tipo de arquivo
    allowed_types = ["image/png", "image/jpeg", "image/jpg", "image/svg+xml"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Tipo de arquivo não suportado. Use PNG, JPG ou SVG. Recebido: {file.content_type}"
        )
    
    # Ler arquivo
    contents = await file.read()
    
    # Validar tamanho (5MB)
    max_size = 5 * 1024 * 1024  # 5MB em bytes
    if len(contents) > max_size:
        raise HTTPException(
            status_code=400,
            detail=f"Arquivo muito grande. Tamanho máximo: 5MB. Tamanho do arquivo: {len(contents) / 1024 / 1024:.2f}MB"
        )
    
    # Converter para base64
    base64_encoded = base64.b64encode(contents).decode('utf-8')
    data_uri = f"data:{file.content_type};base64,{base64_encoded}"
    
    # Atualizar no banco
    db.execute(
        text("UPDATE public.settings SET logo_url = :logo_url, updated_at = now() WHERE id = :id"),
        {"logo_url": data_uri, "id": str(SETTINGS_ID)}
    )
    db.commit()
    
    return {
        "message": "Logo atualizado com sucesso",
        "logo_url": data_uri,
        "file_name": file.filename,
        "file_size": f"{len(contents) / 1024:.2f} KB"
    }
