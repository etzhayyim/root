import unittest
from kotoba_langgraph import _cbor as cbor2
from app import compiled

class TestCRMIntegration(unittest.TestCase):
    def test_close_opportunity_won(self):
        payload = {
            "opportunity_id": "006000000000001AAA",
            "stage_name": "Closed Won"
        }
        initial_state = {
            "input_data": payload,
            "errors": []
        }
        
        result = compiled.invoke(initial_state)
        
        self.assertEqual(result["status"], "SUCCESS")
        self.assertEqual(result["opportunity"].StageName, "Closed Won")
        self.assertEqual(result["opportunity"].Probability, 100.0)

if __name__ == "__main__":
    unittest.main()
