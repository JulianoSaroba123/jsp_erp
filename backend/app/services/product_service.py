"""
Service para Product - regras de negócio.
Camada de validações e lógica de negócio.
"""

from typing import Dict, Optional
from uuid import UUID
from sqlalchemy.orm import Session

from app.models.product import Product
from app.models.user import User
from app.repositories.product_repository import ProductRepository
from app.schemas.product_schema import ProductCreate, ProductUpdate
from app.exceptions.errors import NotFoundError, ValidationError, ConflictError


class ProductService:
    """Service com regras de negócio para produtos."""

    @staticmethod
    def list_products(
        db: Session,
        page: int = 1,
        page_size: int = 20,
        user_id: Optional[UUID] = None,
        q: Optional[str] = None,
        category: Optional[str] = None,
        active: Optional[bool] = None
    ) -> Dict:
        """
        Lista produtos com paginação e filtros.
        
        Args:
            db: Sessão do banco
            page: Página atual (mínimo 1)
            page_size: Itens por página (máximo 100)
            user_id: UUID do usuário (None para admin ver tudo)
            q: Busca por nome ou código
            category: Filtro por categoria
            active: Filtro por status ativo/inativo
        
        Returns:
            {"items": [...], "page": 1, "page_size": 20, "total": 123}
        """
        # Validação: page >= 1
        if page < 1:
            page = 1

        # Proteção de performance: limitar page_size
        if page_size > 100:
            page_size = 100
        if page_size < 1:
            page_size = 1

        # Busca dados
        products = ProductRepository.list_paginated(
            db=db,
            page=page,
            page_size=page_size,
            user_id=user_id,
            q=q,
            category=category,
            active=active
        )
        
        total = ProductRepository.count_total(
            db=db,
            user_id=user_id,
            q=q,
            category=category,
            active=active
        )

        return {
            "items": products,
            "page": page,
            "page_size": page_size,
            "total": total
        }

    @staticmethod
    def get_product(
        db: Session,
        product_id: UUID,
        user_id: Optional[UUID] = None
    ) -> Product:
        """
        Busca produto por ID com validação de acesso.
        
        Args:
            db: Sessão do banco
            product_id: UUID do produto
            user_id: UUID do usuário (None para admin)
        
        Returns:
            Produto encontrado
        
        Raises:
            NotFoundError: Se produto não existe ou usuário não tem acesso (anti-enumeration)
        """
        if user_id:
            # Usuário comum: filtrar por user_id (isolamento)
            product = ProductRepository.get_by_id_and_user(db=db, product_id=product_id, user_id=user_id)
        else:
            # Admin: ver qualquer produto
            product = ProductRepository.get_by_id(db=db, product_id=product_id)
        
        if not product:
            raise NotFoundError(f"Produto {product_id} não encontrado")
        
        return product

    @staticmethod
    def create_product(
        db: Session,
        user_id: UUID,
        data: ProductCreate
    ) -> Product:
        """
        Cria produto com validações de negócio.
        
        Validações:
        1. Usuário deve existir
        2. Code deve ser único (se fornecido) para o mesmo user
        3. Name obrigatório
        4. Preços não negativos (já validado pelo Pydantic)
        
        Args:
            db: Sessão do banco
            user_id: UUID do usuário autenticado
            data: Dados do produto (ProductCreate)
        
        Returns:
            Produto criado
        
        Raises:
            ValidationError: Se dados inválidos
            ConflictError: Se code já existe
        """
        # Validação 1: usuário precisa existir
        user_exists = db.query(User.id).filter(User.id == user_id).first()
        if not user_exists:
            raise ValidationError(f"Usuário {user_id} não encontrado")

        # Validação 2: code único (se fornecido)
        if data.code:
            existing = ProductRepository.get_by_code(db=db, code=data.code, user_id=user_id)
            if existing:
                raise ConflictError(f"Código '{data.code}' já está em uso")

        # Criar produto
        product = ProductRepository.create(
            db=db,
            user_id=user_id,
            code=data.code,
            name=data.name,
            category=data.category,
            unit=data.unit,
            description=data.description,
            cost_price=float(data.cost_price),
            sale_price=float(data.sale_price),
            stock_qty=float(data.stock_qty),
            stock_min=float(data.stock_min),
            active=data.active
        )
        
        return product

    @staticmethod
    def update_product(
        db: Session,
        product_id: UUID,
        user_id: UUID,
        data: ProductUpdate
    ) -> Product:
        """
        Atualiza produto com PATCH parcial.
        
        Regras:
        1. Usuário só pode atualizar seus próprios produtos
        2. Code deve ser único (se alterado)
        3. user_id é IMUTÁVEL
        
        Args:
            db: Sessão do banco
            product_id: UUID do produto
            user_id: UUID do usuário autenticado
            data: Dados para atualizar (ProductUpdate)
        
        Returns:
            Produto atualizado
        
        Raises:
            NotFoundError: Se produto não existe ou não pertence ao usuário
            ConflictError: Se novo code já existe
        """
        # Buscar produto (validar ownership)
        product = ProductRepository.get_by_id_and_user(db=db, product_id=product_id, user_id=user_id)
        if not product:
            raise NotFoundError(f"Produto {product_id} não encontrado")

        # Preparar updates (apenas campos fornecidos)
        updates = {}
        
        if data.code is not None:
            # Validar code único
            if data.code != product.code:
                existing = ProductRepository.get_by_code(
                    db=db,
                    code=data.code,
                    user_id=user_id,
                    exclude_id=product_id
                )
                if existing:
                    raise ConflictError(f"Código '{data.code}' já está em uso")
            updates["code"] = data.code

        if data.name is not None:
            updates["name"] = data.name
        
        if data.category is not None:
            updates["category"] = data.category
        
        if data.unit is not None:
            updates["unit"] = data.unit
        
        if data.description is not None:
            updates["description"] = data.description
        
        if data.cost_price is not None:
            updates["cost_price"] = float(data.cost_price)
        
        if data.sale_price is not None:
            updates["sale_price"] = float(data.sale_price)
        
        if data.stock_qty is not None:
            updates["stock_qty"] = float(data.stock_qty)
        
        if data.stock_min is not None:
            updates["stock_min"] = float(data.stock_min)
        
        if data.active is not None:
            updates["active"] = data.active

        # Aplicar updates
        if updates:
            product = ProductRepository.update(db=db, product=product, **updates)
        
        return product

    @staticmethod
    def delete_product(
        db: Session,
        product_id: UUID,
        user_id: UUID
    ) -> None:
        """
        Soft delete de produto.
        
        Regras:
        1. Usuário só pode deletar seus próprios produtos
        2. Produto já deletado retorna 404 (idempotente)
        
        Args:
            db: Sessão do banco
            product_id: UUID do produto
            user_id: UUID do usuário autenticado
        
        Raises:
            NotFoundError: Se produto não existe ou não pertence ao usuário (anti-enumeration)
        """
        # Buscar produto (validar ownership)
        product = ProductRepository.get_by_id_and_user(db=db, product_id=product_id, user_id=user_id)
        if not product:
            raise NotFoundError(f"Produto {product_id} não encontrado")

        # Soft delete
        ProductRepository.soft_delete(db=db, product=product, deleted_by=user_id)
