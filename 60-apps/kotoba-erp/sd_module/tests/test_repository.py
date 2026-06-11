import unittest
import cbor2
from src.adapters.repository import SDRepository, Quad, kqe
from src.domain.entities import VBRK, VBRP
from datetime import datetime

class TestSDRepository(unittest.TestCase):
    def test_save_billing_document(self):
        captured_quads = []
        def mock_assert_quad(q: Quad) -> None:
            captured_quads.append(q)
            
        kqe.assert_quad = mock_assert_quad
        
        vbrp = VBRP(
            vbeln="INV-001",
            posnr="10",
            aubel="SO-1000",
            aupos="10",
            matnr="MAT-01",
            fkimg=10.0,
            netwr=100.0
        )
        
        vbrk = VBRK(
            vbeln="INV-001",
            fkart="F2",
            kunnr="CUST-01",
            fkdat=datetime(2026, 6, 7),
            netwr=100.0,
            items=[vbrp],
            status="POSTED"
        )
        
        repo = SDRepository("test_sd")
        repo.save_billing_document(vbrk)
        
        self.assertEqual(len(captured_quads), 2)
        self.assertEqual(captured_quads[0].predicate, "erp:sd:vbrk_header")
        
        header_data = cbor2.loads(bytes(captured_quads[0].object_cbor))
        self.assertEqual(header_data["vbeln"], "INV-001")
        self.assertEqual(header_data["fkart"], "F2")

    def test_get_sales_order(self):
        repo = SDRepository("test_sd")
        vbak = repo.get_sales_order("SO-1000")
        
        self.assertIsNotNone(vbak)
        self.assertEqual(vbak.vbeln, "SO-1000")
        self.assertEqual(len(vbak.items), 1)
        self.assertEqual(vbak.items[0].matnr, "MAT-01")

if __name__ == "__main__":
    unittest.main()
