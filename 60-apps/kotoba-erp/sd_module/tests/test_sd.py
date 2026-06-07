import unittest
from kotoba_langgraph import _cbor as cbor2
from app import compiled

class TestSDIntegration(unittest.TestCase):
    def test_generate_billing(self):
        payload = {
            "billing_id": "INV-001",
            "order_id": "SO-1000"
        }
        initial_state = {
            "input_data": payload,
            "errors": []
        }
        
        result = compiled.invoke(initial_state)
        
        self.assertEqual(result["status"], "POSTED")
        self.assertEqual(result["billing_doc"].billing_id, "INV-001")
        self.assertEqual(result["billing_doc"].total_amount, 1000.0)
        self.assertEqual(len(result["billing_doc"].lines), 1)

if __name__ == "__main__":
    unittest.main()
