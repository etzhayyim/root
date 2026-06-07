import unittest
from datetime import datetime
from kotoba_langgraph import _cbor as cbor2
from src.domain.entities import BKPF, BSEG
from src.adapters.repository import FIRepository, Quad, kqe

class TestFIRepository(unittest.TestCase):
    def test_save_accounting_document(self):
        captured_quads = []
        def mock_assert_quad(q: Quad) -> None:
            captured_quads.append(q)
            
        kqe.assert_quad = mock_assert_quad
        
        item1 = BSEG(belnr="DOC-001", buzei="1", hkont="1000", shkzg="S", wrbtr=100.0, sgtxt="Cash")
        item2 = BSEG(belnr="DOC-001", buzei="2", hkont="2000", shkzg="H", wrbtr=100.0, sgtxt="Revenue")
        bkpf = BKPF(belnr="DOC-001", bukrs="1000", bldat=datetime(2026, 6, 7), budat=datetime(2026, 6, 7), items=[item1, item2], bstat="")
        
        repo = FIRepository("test_graph")
        repo.save_accounting_document(bkpf)
        
        self.assertEqual(len(captured_quads), 3)
        self.assertEqual(captured_quads[0].predicate, "erp:fi:bkpf_header")
        
        header_data = cbor2.loads(bytes(captured_quads[0].object_cbor))
        self.assertEqual(header_data["belnr"], "DOC-001")
        self.assertEqual(header_data["bstat"], "")
        
        self.assertEqual(captured_quads[1].predicate, "erp:fi:bseg_item")
        item1_data = cbor2.loads(bytes(captured_quads[1].object_cbor))
        self.assertEqual(item1_data["hkont"], "1000")

    def test_get_accounting_document(self):
        repo = FIRepository("test_graph")
        bkpf = repo.get_accounting_document("DIRECT-001")
        
        self.assertIsNotNone(bkpf)
        self.assertEqual(bkpf.belnr, "DIRECT-001")
        self.assertEqual(bkpf.bukrs, "1000")
        self.assertEqual(len(bkpf.items), 0) # Mock doesn't return items for this test

if __name__ == "__main__":
    unittest.main()
