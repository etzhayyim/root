from dataclasses import dataclass
from typing import List
from datetime import datetime

@dataclass
class Customer:
    customer_id: str
    name: str

@dataclass
class SalesOrderLine:
    material_id: str
    quantity: float
    unit_price: float

@dataclass
class SalesOrder:
    order_id: str
    customer_id: str
    date: datetime
    lines: List[SalesOrderLine]
    status: str = 'OPEN' # 'OPEN', 'DELIVERED', 'BILLED'

@dataclass
class BillingDocumentLine:
    material_id: str
    quantity: float
    unit_price: float
    line_total: float

@dataclass
class BillingDocument:
    billing_id: str
    order_id: str
    customer_id: str
    date: datetime
    lines: List[BillingDocumentLine]
    total_amount: float
    status: str = 'DRAFT' # 'DRAFT', 'POSTED'

    def validate_totals(self) -> bool:
        """Enterprise Business Rule: The total amount must equal the sum of the line totals."""
        calculated_total = sum(line.line_total for line in self.lines)
        return abs(self.total_amount - calculated_total) < 0.0001
