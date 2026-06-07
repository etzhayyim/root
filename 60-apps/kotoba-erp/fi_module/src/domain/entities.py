from typing import List, Optional
from datetime import datetime
from dataclasses import dataclass, field

@dataclass
class Account:
    account_id: str
    name: str
    account_type: str # e.g., 'ASSET', 'LIABILITY', 'EQUITY', 'REVENUE', 'EXPENSE'
    balance: float = 0.0

@dataclass
class JournalEntryLine:
    account_id: str
    amount: float # Positive for Debit, Negative for Credit (or explicit debit/credit)
    is_debit: bool
    description: str

@dataclass
class JournalEntry:
    entry_id: str
    date: datetime
    lines: List[JournalEntryLine]
    status: str = 'DRAFT' # 'DRAFT', 'POSTED', 'REJECTED'

    def validate_balance(self) -> bool:
        """Enterprise Business Rule: A journal entry must balance (Debits == Credits)."""
        debits = sum(line.amount for line in self.lines if line.is_debit)
        credits = sum(line.amount for line in self.lines if not line.is_debit)
        return abs(debits - credits) < 0.0001

