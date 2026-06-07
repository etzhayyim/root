import unittest
from kotoba_langgraph import _cbor as cbor2
from app import compiled

class TestFIIntegration(unittest.TestCase):
    def test_direct_journal(self):
        payload = {
            "entry_id": "DIRECT-001",
            "lines": [
                {"account_id": "1000", "amount": 100.0, "is_debit": True, "description": "Cash"},
                {"account_id": "2000", "amount": 100.0, "is_debit": False, "description": "Revenue"}
            ]
        }
        initial_state = {
            "ctx_payload": payload,
            "validation_errors": []
        }
        
        # Test invocation without writing to KQE in this context,
        # we would mock KQE but repository uses a simple mock if imported outside WASM
        result = compiled.invoke(initial_state)
        
        self.assertEqual(result["status"], "POSTED")
        self.assertEqual(result["journal_entry"].entry_id, "DIRECT-001")
        self.assertEqual(result["route"], "direct_journal")
        
    def test_mm_event_processing(self):
        payload = {
            "event_type": "GoodsReceiptPosted",
            "receipt_id": "GR-001",
            "po_number": "PO-1000",
            "total_value": 105.0,
            "timestamp": "2026-06-07T00:00:00"
        }
        initial_state = {
            "ctx_payload": payload,
            "validation_errors": []
        }
        
        result = compiled.invoke(initial_state)
        
        self.assertEqual(result["status"], "POSTED")
        self.assertEqual(result["route"], "map_mm_receipt")
        self.assertEqual(result["journal_entry"].entry_id, "JE-GR-001")
        
        lines = result["journal_entry"].lines
        self.assertEqual(len(lines), 2)
        
        debit_line = next(l for l in lines if l.is_debit)
        self.assertEqual(debit_line.account_id, "1300")
        self.assertEqual(debit_line.amount, 105.0)
        
        credit_line = next(l for l in lines if not l.is_debit)
        self.assertEqual(credit_line.account_id, "2110")
        self.assertEqual(credit_line.amount, 105.0)

if __name__ == "__main__":
    unittest.main()
