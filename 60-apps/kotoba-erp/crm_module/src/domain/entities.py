from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime

# Salesforce Standard Object: Account
@dataclass
class Account:
    Id: str # 18-char SFDC ID
    Name: str
    Industry: str
    Type: str

# Salesforce Standard Object: Contact
@dataclass
class Contact:
    Id: str
    AccountId: str
    FirstName: str
    LastName: str
    Email: str

# Salesforce Standard Object: Opportunity
@dataclass
class Opportunity:
    Id: str
    AccountId: str
    Name: str
    StageName: str # e.g., 'Prospecting', 'Negotiation/Review', 'Closed Won', 'Closed Lost'
    Amount: float
    CloseDate: datetime
    Probability: float # 0.0 to 100.0

    def is_closed(self) -> bool:
        return self.StageName in ['Closed Won', 'Closed Lost']

    def validate_won(self) -> bool:
        """Business Rule: Won opportunities must have an Amount > 0 and 100% probability."""
        if self.StageName == 'Closed Won':
            return self.Amount > 0 and self.Probability == 100.0
        return True
