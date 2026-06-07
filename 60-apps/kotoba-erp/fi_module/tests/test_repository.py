import unittest
from datetime import datetime
import cbor2
from src.domain.entities import JournalEntry, JournalEntryLine
from src.adapters.repository import JournalEntryRepository, Quad, kqe

class TestJournalEntryRepository(unittest.TestCase):
    def test_save_entry(self):
        # Setup mock quad capturing
        captured_quads = []
        def mock_assert_quad(q: Quad) -> None:
            captured_quads.append(q)
            
        kqe.assert_quad = mock_assert_quad
        
        # Create domain entity
        line1 = JournalEntryLine(account_id="1000", amount=100.0, is_debit=True, description="Cash")
        line2 = JournalEntryLine(account_id="2000", amount=100.0, is_debit=False, description="Revenue")
        entry = JournalEntry(entry_id="JE-001", date=datetime(2026, 6, 7), lines=[line1, line2], status="POSTED")
        
        repo = JournalEntryRepository("test_graph")
        repo.save(entry)
        
        # Verify
        self.assertEqual(len(captured_quads), 3)
        self.assertEqual(captured_quads[0].predicate, "erp:fi:has_header")
        
        header_data = cbor2.loads(bytes(captured_quads[0].object_cbor))
        self.assertEqual(header_data["entry_id"], "JE-001")
        self.assertEqual(header_data["status"], "POSTED")
        
        self.assertEqual(captured_quads[1].predicate, "erp:fi:has_line")
        line1_data = cbor2.loads(bytes(captured_quads[1].object_cbor))
        self.assertEqual(line1_data["account_id"], "1000")
        
        self.assertEqual(captured_quads[2].predicate, "erp:fi:has_line")
        line2_data = cbor2.loads(bytes(captured_quads[2].object_cbor))
        self.assertEqual(line2_data["account_id"], "2000")

if __name__ == "__main__":
    unittest.main()
