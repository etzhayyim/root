from kotoba_langgraph import _cbor as cbor2
from typing import List
from src.domain.entities import JournalEntry

try:
    from wit_world import kqe
    from wit_world.types import Quad
except ImportError:
    # Mock for local testing outside of WASM host
    class Quad:
        def __init__(self, graph: str, subject: str, predicate: str, object_cbor: bytes):
            self.graph = graph
            self.subject = subject
            self.predicate = predicate
            self.object_cbor = object_cbor
    
    class _KqeMock:
        def assert_quad(self, q: Quad) -> None:
            pass # Mocked

    kqe = _KqeMock()

class JournalEntryRepository:
    def __init__(self, graph_name: str = "fi_journal"):
        self.graph_name = graph_name

    def save(self, entry: JournalEntry) -> None:
        """
        Translates a JournalEntry entity into Quad assertions and writes them 
        to the kotoba-kqe engine using the WASM host function.
        """
        # Save entry header
        entry_subject = f"journal_entry:{entry.entry_id}"
        
        # Serialize header fields (status, date) as CBOR
        header_data = {
            "entry_id": entry.entry_id,
            "date": entry.date.isoformat(),
            "status": entry.status,
            "type": "JournalEntry"
        }
        
        kqe.assert_quad(Quad(
            graph=self.graph_name,
            subject=entry_subject,
            predicate="erp:fi:has_header",
            object_cbor=list(cbor2.dumps(header_data))
        ))

        # Save lines
        for idx, line in enumerate(entry.lines):
            line_data = {
                "account_id": line.account_id,
                "amount": line.amount,
                "is_debit": line.is_debit,
                "description": line.description,
                "index": idx
            }
            kqe.assert_quad(Quad(
                graph=self.graph_name,
                subject=entry_subject,
                predicate="erp:fi:has_line",
                object_cbor=list(cbor2.dumps(line_data))
            ))

