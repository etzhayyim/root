import unittest
import cbor2
from src.adapters.repository import MMRepository, Quad, kqe
from src.domain.entities import GoodsReceipt, GoodsReceiptLine

class TestMMRepository(unittest.TestCase):
    def test_save_receipt(self):
        captured_quads = []
        def mock_assert_quad(q: Quad) -> None:
            captured_quads.append(q)
            
        kqe.assert_quad = mock_assert_quad
        
        from datetime import datetime
        receipt = GoodsReceipt(
            receipt_id="GR-001",
            po_number="PO-1000",
            date=datetime(2026, 6, 7),
            lines=[GoodsReceiptLine("MAT-01", 10.0)],
            status="POSTED"
        )
        
        repo = MMRepository("test_mm")
        repo.save_goods_receipt(receipt)
        
        self.assertEqual(len(captured_quads), 2)
        self.assertEqual(captured_quads[0].predicate, "erp:mm:has_receipt_header")
        
        header_data = cbor2.loads(bytes(captured_quads[0].object_cbor))
        self.assertEqual(header_data["receipt_id"], "GR-001")
        self.assertEqual(header_data["po_number"], "PO-1000")

if __name__ == "__main__":
    unittest.main()
