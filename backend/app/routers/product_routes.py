"""
Router de Products - endpoints HTTP.
Responsabilidade: receber requests e chamar ProductService.
NÃO contém lógica de negócio nem queries SQL.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.services.product_service import ProductService
from app.schemas.product_schema import ProductCreate, ProductUpdate, ProductOut, ProductListResponse
from app.security.deps import get_current_user, get_db, require_permission
from app.models.user import User
from app.exceptions.errors import ConflictError, NotFoundError, ValidationError


router = APIRouter(prefix="/products", tags=["Products"])


@router.get("", status_code=status.HTTP_200_OK, response_model=ProductListResponse)
def list_products(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    q: str = Query(None, description="Buscar por nome ou código"),
    category: str = Query(None, description="Filtrar por categoria"),
    active: bool = Query(None, description="Filtrar por status ativo/inativo"),
    current_user: User = Depends(require_permission("products", "read")),
    db: Session = Depends(get_db)
):
    """
    Lista produtos com paginação e filtros.
    
    **Permissão necessária: products:read**
    
    Regras multi-tenant:
    - **admin**: vê todos os produtos
    - **user, technician, finance**: vê apenas seus próprios produtos
    
    Query params:
    - page: número da página (default 1, min 1)
    - page_size: itens por página (default 20, min 1, max 100)
    - q: busca por nome ou código (parcial, case-insensitive)
    - category: filtrar por categoria exata
    - active: true/false para ativos/inativos
    
    Response: ProductListResponse
    {
      "items": [...],
      "page": 1,
      "page_size": 20,
      "total": 123
    }
    """
    try:
        # Multi-tenant: admin vê tudo, outros veem só os seus
        user_id_filter = None if current_user.role == "admin" else current_user.id
        
        result = ProductService.list_products(
            db=db,
            page=page,
            page_size=page_size,
            user_id=user_id_filter,
            q=q,
            category=category,
            active=active
        )
        
        # Converte ORM models para ProductOut (Pydantic)
        items_out = [ProductOut.model_validate(product) for product in result["items"]]
        
        return ProductListResponse(
            items=items_out,
            page=result["page"],
            page_size=result["page_size"],
            total=result["total"]
        )
    
    except Exception as e:
        from app.core.errors import sanitize_error_message
        detail = sanitize_error_message(e, "Erro ao listar produtos")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail
        )


@router.get("/{product_id}", status_code=status.HTTP_200_OK, response_model=ProductOut)
def get_product(
    product_id: UUID,
    current_user: User = Depends(require_permission("products", "read")),
    db: Session = Depends(get_db)
):
    """
    Busca produto por ID.
    
    **Permissão necessária: products:read**
    
    Regras multi-tenant:
    - **admin**: pode ver qualquer produto
    - **user, technician, finance**: só pode ver seus próprios produtos
    
    Anti-enumeration:
    - 404 se produto não existe
    - 404 se produto existe mas não pertence ao usuário (não 403)
    
    Path params:
    - product_id: UUID do produto
    
    Response: ProductOut
    """
    try:
        # Multi-tenant: admin vê tudo, outros veem só os seus
        user_id_filter = None if current_user.role == "admin" else current_user.id
        
        product = ProductService.get_product(
            db=db,
            product_id=product_id,
            user_id=user_id_filter
        )
        
        return ProductOut.model_validate(product)
    
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        from app.core.errors import sanitize_error_message
        detail = sanitize_error_message(e, "Erro ao buscar produto")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail
        )


@router.post("", status_code=status.HTTP_201_CREATED, response_model=ProductOut)
def create_product(
    product_data: ProductCreate,
    current_user: User = Depends(require_permission("products", "create")),
    db: Session = Depends(get_db)
):
    """
    Cria novo produto.
    
    **Permissão necessária: products:create**
    
    Regras multi-tenant:
    - O produto será criado automaticamente para o usuário autenticado
    - user_id é obtido do token JWT (não pode ser fornecido no body)
    
    Body (ProductCreate):
    - code: código interno (opcional, único por usuário)
    - name: nome (obrigatório, 1-200 chars)
    - category: categoria (opcional)
    - unit: unidade (opcional, ex: un, m, kg)
    - description: descrição (opcional)
    - cost_price: preço de custo (default 0, >= 0)
    - sale_price: preço de venda (default 0, >= 0)
    - stock_qty: quantidade em estoque (default 0, >= 0)
    - stock_min: estoque mínimo (default 0, >= 0)
    - active: ativo (default true)
    
    Validações:
    - Code deve ser único para o usuário autenticado
    - Name obrigatório
    - Preços e estoque não negativos
    
    Response: ProductOut (201 Created)
    """
    try:
        product = ProductService.create_product(
            db=db,
            user_id=current_user.id,
            data=product_data
        )
        
        return ProductOut.model_validate(product)
    
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except ConflictError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except Exception as e:
        from app.core.errors import sanitize_error_message
        detail = sanitize_error_message(e, "Erro ao criar produto")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail
        )


@router.patch("/{product_id}", status_code=status.HTTP_200_OK, response_model=ProductOut)
def update_product(
    product_id: UUID,
    product_data: ProductUpdate,
    current_user: User = Depends(require_permission("products", "update")),
    db: Session = Depends(get_db)
):
    """
    Atualiza produto (PATCH parcial).
    
    **Permissão necessária: products:update**
    
    Regras multi-tenant:
    - Usuário só pode atualizar seus próprios produtos
    - user_id é IMUTÁVEL (não pode ser alterado)
    
    Anti-enumeration:
    - 404 se produto não existe ou não pertence ao usuário (não 403)
    
    Path params:
    - product_id: UUID do produto
    
    Body (ProductUpdate - todos opcionais):
    - code: novo código (validação de unicidade)
    - name: novo nome
    - category: nova categoria
    - unit: nova unidade
    - description: nova descrição
    - cost_price: novo preço de custo
    - sale_price: novo preço de venda
    - stock_qty: nova quantidade em estoque
    - stock_min: novo estoque mínimo
    - active: novo status ativo/inativo
    
    Validações:
    - Se code for alterado, deve ser único para o usuário
    - Name não pode ser vazio
    - Preços e estoque não negativos
    
    Response: ProductOut (200 OK)
    """
    try:
        product = ProductService.update_product(
            db=db,
            product_id=product_id,
            user_id=current_user.id,
            data=product_data
        )
        
        return ProductOut.model_validate(product)
    
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except ConflictError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except Exception as e:
        from app.core.errors import sanitize_error_message
        detail = sanitize_error_message(e, "Erro ao atualizar produto")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail
        )


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(
    product_id: UUID,
    current_user: User = Depends(require_permission("products", "delete")),
    db: Session = Depends(get_db)
):
    """
    Deleta produto (soft delete).
    
    **Permissão necessária: products:delete**
    
    Regras multi-tenant:
    - Usuário só pode deletar seus próprios produtos
    - Soft delete: produto não é removido fisicamente, apenas marcado como deleted_at
    
    Anti-enumeration:
    - 404 se produto não existe ou não pertence ao usuário (não 403)
    
    Path params:
    - product_id: UUID do produto
    
    Response: 204 No Content (sem body)
    """
    try:
        ProductService.delete_product(
            db=db,
            product_id=product_id,
            user_id=current_user.id
        )
        
        # 204 No Content - sem retorno
        return None
    
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        from app.core.errors import sanitize_error_message
        detail = sanitize_error_message(e, "Erro ao deletar produto")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail
        )
