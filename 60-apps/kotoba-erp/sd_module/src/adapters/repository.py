from kotoba_langgraph import _cbor as cbor2
from typing import Optional
from datetime import datetime
from src.domain.entities import VBAK, VBAP, VBRK, VBRP

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
        def get_objects(self, graph: str, subject: str, predicate: str) -> list[bytes]:
            if predicate == "erp:sd:vbak_header":
                return [cbor2.dumps({
                    "vbeln": "SO-1000",
                    "kunnr": "CUST-01",
                    "audat": datetime.now().isoformat(),
                    "status": "OPEN"
                })]
            if predicate == "erp:sd:vbap_item":
                return [cbor2.dumps({
                    "vbeln": "SO-1000",
                    "posnr": "10",
                    "matnr": "MAT-01",
                    "kwmeng": 10.0,
                    "netpr": 100.0
                })]
            return []
        
    class _KseMock:
        def publish(self, topic: str, payload: bytes) -> str: return "mock-cid"

    kqe = _KqeMock()
    kse = _KseMock()

class SDRepository:
    def __init__(self, graph_name: str = "sd_sales"):
        self.graph_name = graph_name

    def get_sales_order(self, vbeln: str) -> Optional[VBAK]:
        """Fetch VBAK and VBAP from KQE using true read API (`get_objects`)."""
        subject = f"vbak:{vbeln}"
        
        header_objs = kqe.get_objects(self.graph_name, subject, "erp:sd:vbak_header")
        if not header_objs:
            return None
            
        header_data = cbor2.loads(bytes(header_objs[0]))
        
        item_objs = kqe.get_objects(self.graph_name, subject, "erp:sd:vbap_item")
        items = []
        for obj_bytes in item_objs:
            item_data = cbor2.loads(bytes(obj_bytes))
            items.append(VBAP(
                vbeln=item_data["vbeln"],
                posnr=item_data["posnr"],
                matnr=item_data["matnr"],
                kwmeng=item_data["kwmeng"],
                netpr=item_data["netpr"]
            ))
            
        return VBAK(
            vbeln=header_data["vbeln"],
            kunnr=header_data["kunnr"],
            audat=datetime.fromisoformat(header_data["audat"]),
            items=items,
            status=header_data["status"]
        )

    def save_billing_document(self, vbrk: VBRK) -> None:
        """Persist Billing Document (VBRK/VBRP) to Kotoba KQE and publish to KSE."""
        vbeln_subject = f"vbrk:{vbrk.vbeln}"
        
        header_data = {
            "vbeln": vbrk.vbeln,
            "fkart": vbrk.fkart,
            "kunnr": vbrk.kunnr,
            "fkdat": vbrk.fkdat.isoformat(),
            "netwr": vbrk.netwr,
            "status": vbrk.status
        }
        
        kqe.assert_quad(Quad(
            graph=self.graph_name,
            subject=vbeln_subject,
            predicate="erp:sd:vbrk_header",
            object_cbor=list(cbor2.dumps(header_data))
        ))

        for item in vbrk.items:
            item_data = {
                "vbeln": item.vbeln,
                "posnr": item.posnr,
                "aubel": item.aubel,
                "aupos": item.aupos,
                "matnr": item.matnr,
                "fkimg": item.fkimg,
                "netwr": item.netwr
            }
            kqe.assert_quad(Quad(
                graph=self.graph_name,
                subject=vbeln_subject,
                predicate="erp:sd:vbrp_item",
                object_cbor=list(cbor2.dumps(item_data))
            ))
            
        # Publish an event to the stream engine for the FI module to pick up (AR/Revenue)
        event_payload = {
            "event_type": "BillingDocumentPosted",
            "vbeln": vbrk.vbeln,
            "aubel": vbrk.items[0].aubel if vbrk.items else "",
            "kunnr": vbrk.kunnr,
            "netwr": vbrk.netwr,
            "timestamp": vbrk.fkdat.isoformat()
        }
        kse.publish("erp.sd.billing", list(cbor2.dumps(event_payload)))
