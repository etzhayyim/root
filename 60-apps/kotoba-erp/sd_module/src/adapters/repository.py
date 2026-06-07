from kotoba_langgraph import _cbor as cbor2
from typing import Optional
from src.domain.entities import SalesOrder, SalesOrderLine, BillingDocument

try:
    from wit_world import kqe, kse
    from wit_world.types import Quad
except ImportError:
    class Quad:
        def __init__(self, graph: str, subject: str, predicate: str, object_cbor: bytes):
            self.graph = graph
            self.subject = subject
            self.predicate = predicate
            self.object_cbor = object_cbor
            
    class _KqeMock:
        def assert_quad(self, q: Quad) -> None: pass
        def get_objects(self, graph: str, subject: str, predicate: str) -> list[bytes]: return []
        
    class _KseMock:
        def publish(self, topic: str, payload: bytes) -> str: return "mock-cid"

    kqe = _KqeMock()
    kse = _KseMock()

class SDRepository:
    def __init__(self, graph_name: str = "sd_sales"):
        self.graph_name = graph_name

    def get_sales_order(self, order_id: str) -> Optional[SalesOrder]:
        """Fetch Sales Order from KQE (mocked logic for prototype)."""
        if order_id == "SO-1000":
            from datetime import datetime
            return SalesOrder(
                order_id="SO-1000",
                customer_id="CUST-01",
                date=datetime.now(),
                lines=[SalesOrderLine("MAT-01", 10.0, 100.0)]
            )
        return None

    def save_billing_document(self, billing: BillingDocument) -> None:
        """Persist Billing Document to Kotoba KQE and publish to KSE."""
        billing_subject = f"billing:{billing.billing_id}"
        
        header_data = {
            "billing_id": billing.billing_id,
            "order_id": billing.order_id,
            "customer_id": billing.customer_id,
            "date": billing.date.isoformat(),
            "total_amount": billing.total_amount,
            "status": billing.status
        }
        
        kqe.assert_quad(Quad(
            graph=self.graph_name,
            subject=billing_subject,
            predicate="erp:sd:has_billing_header",
            object_cbor=list(cbor2.dumps(header_data))
        ))

        for idx, line in enumerate(billing.lines):
            line_data = {
                "material_id": line.material_id,
                "quantity": line.quantity,
                "unit_price": line.unit_price,
                "line_total": line.line_total,
                "index": idx
            }
            kqe.assert_quad(Quad(
                graph=self.graph_name,
                subject=billing_subject,
                predicate="erp:sd:has_billing_line",
                object_cbor=list(cbor2.dumps(line_data))
            ))
            
        # Publish an event to the stream engine for the FI module to pick up (AR/Revenue)
        event_payload = {
            "event_type": "BillingDocumentPosted",
            "billing_id": billing.billing_id,
            "order_id": billing.order_id,
            "customer_id": billing.customer_id,
            "total_amount": billing.total_amount,
            "timestamp": billing.date.isoformat()
        }
        kse.publish("erp.sd.billing", list(cbor2.dumps(event_payload)))
