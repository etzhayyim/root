import unittest
import cbor2
from src.adapters.repository import MMRepository, Quad, kqe
from src.domain.entities import MKPF, MSEG
from datetime import datetime

class TestMMRepository(unittest.TestCase):
    def test_save_receipt(self):
        captured_quads = []
        def mock_assert_quad(q: Quad) -> None:
            captured_quads.append(q)
            
        kqe.assert_quad = mock_assert_quad
        
        mseg = MSEG(
            mblnr="GR-001",
            zeile="1",
            bwart="101",
            matnr="MAT-01",
            menge=10.0,
            ebeln="PO-1000",
            ebelp="10"
        )
        
        mkpf = MKPF(
            mblnr="GR-001",
            budat=datetime(2026, 6, 7),
            usnam="TEST_USER",
            items=[mseg],
            status="POSTED"
        )
        
        repo = MMRepository("test_mm")
        repo.save_material_document(mkpf)
        
        self.assertEqual(len(captured_quads), 2)
        self.assertEqual(captured_quads[0].predicate, "erp:mm:mkpf_header")
        
        header_data = cbor2.loads(bytes(captured_quads[0].object_cbor))
        self.assertEqual(header_data["mblnr"], "GR-001")
        self.assertEqual(header_data["usnam"], "TEST_USER")

    def test_get_purchase_order(self):
        repo = MMRepository("test_mm")
        ekko = repo.get_purchase_order("PO-1000")
        
        self.assertIsNotNone(ekko)
        self.assertEqual(ekko.ebeln, "PO-1000")
        self.assertEqual(len(ekko.items), 1)
        self.assertEqual(ekko.items[0].matnr, "MAT-01")

if __name__ == "__main__":
    unittest.main()
