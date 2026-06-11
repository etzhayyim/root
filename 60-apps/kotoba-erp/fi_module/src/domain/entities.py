from typing import List, Optional
from datetime import datetime
from dataclasses import dataclass, field

# SAP Standard Model: SKA1 (G/L Account Master)
@dataclass
class SKA1:
    saknr: str # G/L Account Number
    txt20: str # G/L Account Short Text
    xbilk: bool # Indicator: Account is a balance sheet account?

# SAP Standard Model: BSEG (Accounting Document Segment)
@dataclass
class BSEG:
    belnr: str # Accounting Document Number
    buzei: str # Number of Line Item Within Accounting Document
    hkont: str # General Ledger Account
    shkzg: str # Debit/Credit Indicator ('H' for Credit, 'S' for Debit)
    wrbtr: float # Amount in document currency
    sgtxt: str # Item Text

# SAP Standard Model: BKPF (Accounting Document Header)
@dataclass
class BKPF:
    belnr: str # Accounting Document Number
    bukrs: str # Company Code
    bldat: datetime # Document Date in Document
    budat: datetime # Posting Date in the Document
    items: List[BSEG]
    bstat: str = 'V' # Document Status ('V' = Parked/Draft, '' = Posted)

    def validate_balance(self) -> bool:
        """Enterprise Business Rule: A journal entry must balance (Debits == Credits)."""
        debits = sum(item.wrbtr for item in self.items if item.shkzg == 'S')
        credits = sum(item.wrbtr for item in self.items if item.shkzg == 'H')
        return abs(debits - credits) < 0.0001
