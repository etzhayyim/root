from dataclasses import dataclass
from typing import List
from datetime import datetime

@dataclass
class Material:
    material_id: str
    name: str
    unit_of_measure: str

@dataclass
class PurchaseOrderLine:
    material_id: str
    quantity: float
    price_per_unit: float

@dataclass
class PurchaseOrder:
    po_number: str
    vendor_id: str
    lines: List[PurchaseOrderLine]
    status: str = 'OPEN' # 'OPEN', 'RECEIVED', 'CLOSED'

@dataclass
class GoodsReceiptLine:
    material_id: str
    received_quantity: float

@dataclass
class GoodsReceipt:
    receipt_id: str
    po_number: str
    date: datetime
    lines: List[GoodsReceiptLine]
    status: str = 'DRAFT' # 'DRAFT', 'POSTED'

    def validate_receipt(self, po: PurchaseOrder) -> bool:
        """Enterprise Business Rule: Goods receipt must match a valid PO and not exceed ordered quantity."""
        # Simple validation for prototype: check if materials exist in PO
        po_materials = {line.material_id: line.quantity for line in po.lines}
        for line in self.lines:
            if line.material_id not in po_materials:
                return False
            # Check quantity (simplification: exact match or partial)
            if line.received_quantity <= 0 or line.received_quantity > po_materials[line.material_id]:
                return False
        return True
