"""
Repository para Product - acesso a dados.
Camada exclusiva de persistência (queries SQLAlchemy).
"""

from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
from uuid import UUID

from app.models.product import Product


class ProductRepository:
    """Repositório com queries de Product."""

    @staticmethod
    def list_paginated(
        db: Session, 
        page: int, 
        page_size: int, 
        user_id: Optional[UUID] = None,
        q: Optional[str] = None,
        category: Optional[str] = None,
        active: Optional[bool] = None,
        include_deleted: bool = False
    ) -> List[Product]:
        """
        Lista produtos com paginação e filtros.
        
        Args:
            db: Sessão do banco
            page: Página atual
            page_size: Itens por página
            user_id: UUID do usuário (None para admin ver tudo)
            q: Busca por nome ou código
            category: Filtro por categoria
            active: Filtro por status ativo/inativo
            include_deleted: Se True, inclui soft-deleted
        
        Returns:
            Lista de produtos ordenados por created_at desc
        """
        offset = (page - 1) * page_size
        query = db.query(Product)
        
        # Soft delete
        if not include_deleted:
            query = query.filter(Product.deleted_at.is_(None))
        
        # Isolamento por user_id (admin vê tudo)
        if user_id:
            query = query.filter(Product.user_id == user_id)
        
        # Filtros
        if q:
            search_term = f"%{q}%"
            query = query.filter(
                or_(
                    Product.name.ilike(search_term),
                    Product.code.ilike(search_term)
                )
            )
        
        if category:
            query = query.filter(Product.category == category)
        
        if active is not None:
            query = query.filter(Product.active == active)
        
        return (
            query
            .order_by(Product.created_at.desc())
            .offset(offset)
            .limit(page_size)
            .all()
        )

    @staticmethod
    def count_total(
        db: Session,
        user_id: Optional[UUID] = None,
        q: Optional[str] = None,
        category: Optional[str] = None,
        active: Optional[bool] = None,
        include_deleted: bool = False
    ) -> int:
        """Conta total de produtos com os mesmos filtros do list_paginated."""
        query = db.query(Product)
        
        if not include_deleted:
            query = query.filter(Product.deleted_at.is_(None))
        
        if user_id:
            query = query.filter(Product.user_id == user_id)
        
        if q:
            search_term = f"%{q}%"
            query = query.filter(
                or_(
                    Product.name.ilike(search_term),
                    Product.code.ilike(search_term)
                )
            )
        
        if category:
            query = query.filter(Product.category == category)
        
        if active is not None:
            query = query.filter(Product.active == active)
        
        return query.count()

    @staticmethod
    def get_by_id(db: Session, product_id: UUID, include_deleted: bool = False) -> Optional[Product]:
        """
        Busca produto por ID.
        
        Retorna None se não existir ou estiver soft-deleted (exceto se include_deleted=True).
        """
        query = db.query(Product).filter(Product.id == product_id)
        if not include_deleted:
            query = query.filter(Product.deleted_at.is_(None))
        return query.first()

    @staticmethod
    def get_by_id_and_user(
        db: Session, 
        product_id: UUID, 
        user_id: UUID,
        include_deleted: bool = False
    ) -> Optional[Product]:
        """
        Busca produto por ID com filtro multi-tenant.
        
        Retorna None se:
        - Product não existe
        - Product não pertence ao user_id fornecido
        - Product está soft-deleted (exceto se include_deleted=True)
        
        Usado para anti-enumeration (404 para todos os casos).
        """
        query = db.query(Product).filter(
            Product.id == product_id,
            Product.user_id == user_id
        )
        if not include_deleted:
            query = query.filter(Product.deleted_at.is_(None))
        return query.first()

    @staticmethod
    def get_by_code(
        db: Session, 
        code: str, 
        user_id: Optional[UUID] = None,
        exclude_id: Optional[UUID] = None
    ) -> Optional[Product]:
        """
        Busca produto por código.
        
        Args:
            db: Sessão do banco
            code: Código do produto
            user_id: UUID do usuário (para validar duplicidade no mesmo user)
            exclude_id: Excluir produto com esse ID (usado em updates)
        
        Returns:
            Produto encontrado ou None
        """
        query = db.query(Product).filter(
            Product.code == code,
            Product.deleted_at.is_(None)
        )
        
        if user_id:
            query = query.filter(Product.user_id == user_id)
        
        if exclude_id:
            query = query.filter(Product.id != exclude_id)
        
        return query.first()

    @staticmethod
    def create(
        db: Session,
        user_id: UUID,
        code: Optional[str],
        name: str,
        category: Optional[str],
        unit: Optional[str],
        description: Optional[str],
        cost_price: float,
        sale_price: float,
        stock_qty: float,
        stock_min: float,
        active: bool
    ) -> Product:
        """
        Cria novo produto.
        
        Fluxo:
        - db.add(): adiciona na sessão (staging)
        - db.commit(): executa INSERT no banco
        - db.refresh(): recarrega objeto com valores gerados (id, created_at, etc)
        """
        product = Product(
            user_id=user_id,
            code=code,
            name=name,
            category=category,
            unit=unit,
            description=description,
            cost_price=cost_price,
            sale_price=sale_price,
            stock_qty=stock_qty,
            stock_min=stock_min,
            active=active
        )

        db.add(product)
        db.commit()
        db.refresh(product)

        return product

    @staticmethod
    def update(db: Session, product: Product, **kwargs) -> Product:
        """
        Atualiza produto com campos fornecidos em kwargs.
        
        Fluxo:
        - Atualiza atributos do objeto ORM
        - db.commit(): executa UPDATE no banco
        - db.refresh(): recarrega objeto atualizado
        """
        for key, value in kwargs.items():
            if hasattr(product, key):
                setattr(product, key, value)
        
        db.commit()
        db.refresh(product)
        
        return product

    @staticmethod
    def soft_delete(db: Session, product: Product, deleted_by: UUID) -> Product:
        """
        Marca produto como deletado (soft delete).
        
        Define deleted_at = now() e deleted_by.
        Não remove fisicamente do banco.
        """
        from datetime import datetime
        
        product.deleted_at = datetime.utcnow()
        product.deleted_by = deleted_by
        
        db.commit()
        db.refresh(product)
        
        return product
