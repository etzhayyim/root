from dataclasses import dataclass
from typing import List
from datetime import datetime

# SAP Standard Model: VBAK (Sales Document Header)
@dataclass
class VBAK:
    vbeln: str # Sales and Distribution Document Number
    kunnr: str # Sold-to party (Customer)
    audat: datetime # Document Date
    items: List['VBAP']
    status: str = 'OPEN'

# SAP Standard Model: VBAP (Sales Document Item)
@dataclass
class VBAP:
    vbeln: str # Sales Document
    posnr: str # Sales Document Item
    matnr: str # Material Number
    kwmeng: float # Cumulative Order Quantity
    netpr: float # Net Price

# SAP Standard Model: VBRK (Billing Document Header)
@dataclass
class VBRK:
    vbeln: str # Billing Document
    fkart: str # Billing Type (e.g., 'F2' for Invoice)
    kunnr: str # Payer
    fkdat: datetime # Billing Date
    netwr: float # Net Value
    items: List['VBRP']
    status: str = 'DRAFT'

    def validate_totals(self) -> bool:
        """Enterprise Business Rule: The total amount must equal the sum of the line totals."""
        calculated_total = sum(item.netwr for item in self.items)
        return abs(self.netwr - calculated_total) < 0.0001

# SAP Standard Model: VBRP (Billing Document Item)
@dataclass
class VBRP:
    vbeln: str # Billing Document
    posnr: str # Billing Item
    aubel: str # Sales Document (Reference to VBAK)
    aupos: str # Sales Document Item (Reference to VBAP)
    matnr: str # Material Number
    fkimg: float # Actual Invoiced Quantity
    netwr: float # Net Value of the Billing Item
