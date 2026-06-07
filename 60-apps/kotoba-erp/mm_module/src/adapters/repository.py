from kotoba_langgraph import _cbor as cbor2
from typing import Optional
from src.domain.entities import PurchaseOrder, PurchaseOrderLine, GoodsReceipt

try:
    from wit_world import kqe, kse
    from wit_world.types import Quad
except ImportError:
    # Mock for local testing
    class Quad:
        def __init__(self, graph: str, subject: str, predicate: str, object_cbor: bytes):
            self.graph = graph
            self.subject = subject
            self.predicate = predicate
            self.object_cbor = object_cbor
    
    class _KqeMock:
        def assert_quad(self, q: Quad) -> None:
            pass # Mocked
        def get_objects(self, graph: str, subject: str, predicate: str) -> list[bytes]:
            return [] # Mocked

    class _KseMock:
        def publish(self, topic: str, payload: bytes) -> str:
            return "mock-cid"

    kqe = _KqeMock()
    kse = _KseMock()

class MMRepository:
    def __init__(self, graph_name: str = "mm_inventory"):
        self.graph_name = graph_name

    def get_purchase_order(self, po_number: str) -> Optional[PurchaseOrder]:
        """Fetch PO from KQE (mocked logic for prototype)."""
        subject = f"po:{po_number}"
        if po_number == "PO-1000":
            return PurchaseOrder(
                po_number="PO-1000",
                vendor_id="V-001",
                lines=[PurchaseOrderLine("MAT-01", 100.0, 10.50)]
            )
        return None

    def save_goods_receipt(self, receipt: GoodsReceipt) -> None:
        """Persist Goods Receipt to Kotoba KQE and publish to KSE."""
        receipt_subject = f"gr:{receipt.receipt_id}"
        
        header_data = {
            "receipt_id": receipt.receipt_id,
            "po_number": receipt.po_number,
            "date": receipt.date.isoformat(),
            "status": receipt.status
        }
        
        kqe.assert_quad(Quad(
            graph=self.graph_name,
            subject=receipt_subject,
            predicate="erp:mm:has_receipt_header",
            object_cbor=list(cbor2.dumps(header_data))
        ))

        total_value = 0.0
        # In a real app we'd get price from PO or Material Master.
        # Hardcoding a price for the mock prototype.
        mock_price = 10.50 

        for idx, line in enumerate(receipt.lines):
            line_data = {
                "material_id": line.material_id,
                "received_quantity": line.received_quantity,
                "index": idx
            }
            total_value += line.received_quantity * mock_price

            kqe.assert_quad(Quad(
                graph=self.graph_name,
                subject=receipt_subject,
                predicate="erp:mm:has_receipt_line",
                object_cbor=list(cbor2.dumps(line_data))
            ))
            
        # Publish an event to the stream engine for the FI module to pick up
        event_payload = {
            "event_type": "GoodsReceiptPosted",
            "receipt_id": receipt.receipt_id,
            "po_number": receipt.po_number,
            "total_value": total_value,
            "timestamp": receipt.date.isoformat()
        }
        kse.publish("erp.mm.goods_receipt", list(cbor2.dumps(event_payload)))
