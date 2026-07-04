"""
Model SQLAlchemy para tabela core.products
"""
from sqlalchemy import Column, String, Text, Numeric, Boolean, TIMESTAMP, ForeignKey, text, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class Product(Base):
    """
    Tabela de produtos.
    Schema: core
    
    Isolamento: user_id (admin vê tudo, usuários veem apenas seus produtos)
    Soft delete: deleted_at
    """
    __tablename__ = "products"
    __table_args__ = (
        CheckConstraint("cost_price >= 0", name="check_product_cost_price_positive"),
        CheckConstraint("sale_price >= 0", name="check_product_sale_price_positive"),
        CheckConstraint("stock_qty >= 0", name="check_product_stock_qty_positive"),
        CheckConstraint("stock_min >= 0", name="check_product_stock_min_positive"),
        CheckConstraint("peso IS NULL OR peso >= 0", name="check_product_peso_positive"),
        CheckConstraint("markup IS NULL OR (markup >= 0 AND markup <= 1000)", name="check_product_markup_valid"),
        CheckConstraint("margem_lucro IS NULL OR (margem_lucro >= -100 AND margem_lucro <= 1000)", name="check_product_margem_lucro_valid"),
        CheckConstraint("estoque_maximo IS NULL OR estoque_maximo >= 0", name="check_product_estoque_maximo_positive"),
        {"schema": "core"}
    )

    # Colunas
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()")
    )
    
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("core.users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    code = Column(String(50), nullable=True, index=True)  # Código interno do produto
    name = Column(String(200), nullable=False, index=True)
    category = Column(String(80), nullable=True, index=True)
    subcategoria = Column(String(80), nullable=True, index=True)  # Hierarquia de categorização
    unit = Column(String(20), nullable=True)  # un, m, kg, etc
    description = Column(Text, nullable=True)
    
    # Identificação Estendida (do sistema legado)
    codigo_barras = Column(String(50), nullable=True, unique=True, index=True)  # Código de barras
    marca = Column(String(100), nullable=True, index=True)  # Marca do produto
    modelo = Column(String(100), nullable=True)  # Modelo do produto
    
    # Características Físicas
    peso = Column(Numeric(10, 3), nullable=True)  # Peso em kg
    dimensoes = Column(String(100), nullable=True)  # Ex: "10x20x30 cm"
    
    # Preços
    cost_price = Column(Numeric(12, 2), nullable=False, server_default=text("0"))
    sale_price = Column(Numeric(12, 2), nullable=False, server_default=text("0"))
    markup = Column(Numeric(5, 2), nullable=True)  # Percentual de markup (ex: 30.00 = 30%)
    margem_lucro = Column(Numeric(5, 2), nullable=True)  # Percentual de margem de lucro
    
    # Estoque
    stock_qty = Column(Numeric(12, 3), nullable=False, server_default=text("0"))
    stock_min = Column(Numeric(12, 3), nullable=False, server_default=text("0"))
    estoque_maximo = Column(Numeric(12, 3), nullable=True)  # Estoque máximo
    controla_estoque = Column(Boolean, nullable=False, server_default=text("true"))  # Ativar/desativar controle
    
    # Relacionamentos e Observações
    fornecedor_id = Column(UUID(as_uuid=True), nullable=True)  # FK para fornecedores (futuro)
    observacoes = Column(Text, nullable=True)  # Notas gerais sobre o produto
    
    # Status
    active = Column(Boolean, nullable=False, server_default=text("true"))
    
    # Timestamps
    created_at = Column(TIMESTAMP, server_default=text("now()"))
    updated_at = Column(TIMESTAMP, nullable=True, onupdate=text("now()"))
    
    # Soft Delete
    deleted_at = Column(TIMESTAMP, nullable=True, index=True)
    deleted_by = Column(
        UUID(as_uuid=True),
        ForeignKey("core.users.id", ondelete="SET NULL"),
        nullable=True
    )

    # Relacionamentos
    user = relationship("User", foreign_keys=[user_id], lazy="select")
    deleted_by_user = relationship("User", foreign_keys=[deleted_by], lazy="select")
    
    # Propriedades Computed (do sistema legado)
    @property
    def valor_estoque(self) -> float:
        """Valor total do estoque (stock_qty * cost_price)"""
        if self.stock_qty and self.cost_price:
            return float(self.stock_qty * self.cost_price)
        return 0.0
    
    @property
    def situacao_estoque(self) -> str:
        """Situação do estoque: 'baixo', 'normal', 'alto'"""
        if not self.controla_estoque:
            return "sem_controle"
        
        if self.stock_qty <= self.stock_min:
            return "baixo"
        elif self.estoque_maximo and self.stock_qty >= self.estoque_maximo:
            return "alto"
        else:
            return "normal"
    
    @property
    def margem_lucro_calculada(self) -> float:
        """Calcula margem de lucro real: ((venda - custo) / custo) * 100"""
        if self.cost_price and self.cost_price > 0 and self.sale_price:
            return float(((self.sale_price - self.cost_price) / self.cost_price) * 100)
        return 0.0
    
    # Métodos auxiliares (do sistema legado)
    def calcular_preco_venda_por_markup(self) -> float:
        """Calcula preço de venda baseado no markup: custo * (1 + markup/100)"""
        if self.cost_price and self.markup:
            return float(self.cost_price * (1 + self.markup / 100))
        return 0.0
    
    def atualizar_estoque(self, quantidade: float, tipo: str = "adicionar"):
        """
        Atualiza quantidade em estoque
        tipo: 'adicionar' ou 'subtrair'
        """
        if not self.controla_estoque:
            return
        
        if tipo == "adicionar":
            self.stock_qty += quantidade
        elif tipo == "subtrair":
            self.stock_qty -= quantidade
            if self.stock_qty < 0:
                self.stock_qty = 0

    def __repr__(self):
        return f"<Product(id={self.id}, name={self.name}, code={self.code})>"
