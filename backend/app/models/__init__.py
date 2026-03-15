"""
Models Package

Exports all SQLAlchemy models for the application.
"""
from app.models.user import User
from app.models.order import Order
from app.models.financial_entry import FinancialEntry
from app.models.audit_log import AuditLog
# Import Role before Permission (circular dependency - Permission imports from role.py)
from app.models.role import Role
from app.models.permission import Permission
from app.models.customer import Customer
from app.models.product import Product
from app.models.proposal import Proposal, ProposalItem, ProposalProduct
from app.models.service_order import (
    ServiceOrder,
    ServiceOrderItem,
    ServiceOrderProduct,
    ServiceOrderInstallment,
    ServiceOrderAttachment,
)

__all__ = [
    "User",
    "Order",
    "FinancialEntry",
    "AuditLog",
    "Role",
    "Permission",
    "Customer",
    "Product",
    "Proposal",
    "ProposalItem",
    "ProposalProduct",
    "ServiceOrder",
    "ServiceOrderItem",
    "ServiceOrderProduct",
    "ServiceOrderInstallment",
    "ServiceOrderAttachment",
]
