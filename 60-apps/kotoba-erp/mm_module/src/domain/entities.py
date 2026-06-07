from dataclasses import dataclass
from typing import List
from datetime import datetime

# SAP Standard Model: MARA (Material Master Data)
@dataclass
class MARA:
    matnr: str # Material Number
    maktx: str # Material Description
    meins: str # Base Unit of Measure

# SAP Standard Model: EKPO (Purchasing Document Item)
@dataclass
class EKPO:
    ebeln: str # Purchasing Document Number
    ebelp: str # Item Number of Purchasing Document
    matnr: str # Material Number
    menge: float # Purchase Order Quantity
    netpr: float # Net Price

# SAP Standard Model: EKKO (Purchasing Document Header)
@dataclass
class EKKO:
    ebeln: str # Purchasing Document Number
    lifnr: str # Vendor Account Number
    bedat: datetime # Purchasing Document Date
    items: List[EKPO]
    status: str = 'OPEN'

# SAP Standard Model: MSEG (Document Segment: Material)
@dataclass
class MSEG:
    mblnr: str # Number of Material Document
    zeile: str # Item in Material Document
    bwart: str # Movement Type (e.g., '101' for Goods Receipt)
    matnr: str # Material Number
    menge: float # Quantity
    ebeln: str # Purchase Order Number
    ebelp: str # Purchase Order Item

# SAP Standard Model: MKPF (Header: Material Document)
@dataclass
class MKPF:
    mblnr: str # Number of Material Document
    budat: datetime # Posting Date in the Document
    usnam: str # User Name
    items: List[MSEG]
    status: str = 'DRAFT'

    def validate_receipt(self, po: EKKO) -> bool:
        """Enterprise Business Rule: Goods receipt must match a valid PO and not exceed ordered quantity."""
        # Simple validation: mapping PO items by Material Number (in a real system, map by EBELP)
        po_materials = {item.matnr: item.menge for item in po.items}
        for item in self.items:
            if item.matnr not in po_materials:
                return False
            # Ensure we are not receiving more than ordered
            if item.menge <= 0 or item.menge > po_materials[item.matnr]:
                return False
        return True
