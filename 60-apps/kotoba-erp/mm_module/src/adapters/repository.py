from kotoba_langgraph import _cbor as cbor2
from typing import Optional
from datetime import datetime
from src.domain.entities import EKKO, EKPO, MKPF, MSEG

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
        def assert_quad(self, q: Quad) -> None: pass
        def get_objects(self, graph: str, subject: str, predicate: str) -> list[bytes]:
            # Mock KQE get_objects response if testing outside WASM
            if predicate == "erp:mm:ekko_header":
                return [cbor2.dumps({
                    "ebeln": "PO-1000",
                    "lifnr": "V-001",
                    "bedat": datetime.now().isoformat(),
                    "status": "OPEN"
                })]
            if predicate == "erp:mm:ekpo_item":
                return [cbor2.dumps({
                    "ebeln": "PO-1000",
                    "ebelp": "10",
                    "matnr": "MAT-01",
                    "menge": 100.0,
                    "netpr": 10.50
                })]
            return []

    class _KseMock:
        def publish(self, topic: str, payload: bytes) -> str: return "mock-cid"

    kqe = _KqeMock()
    kse = _KseMock()

class MMRepository:
    def __init__(self, graph_name: str = "mm_inventory"):
        self.graph_name = graph_name

    def get_purchase_order(self, ebeln: str) -> Optional[EKKO]:
        """Fetch EKKO and EKPO from KQE using true read API (`get_objects`)."""
        subject = f"ekko:{ebeln}"
        
        # Call host API to read objects matching subject/predicate
        header_objs = kqe.get_objects(self.graph_name, subject, "erp:mm:ekko_header")
        if not header_objs:
            return None
            
        header_data = cbor2.loads(bytes(header_objs[0]))
        
        # Read items
        item_objs = kqe.get_objects(self.graph_name, subject, "erp:mm:ekpo_item")
        items = []
        for obj_bytes in item_objs:
            item_data = cbor2.loads(bytes(obj_bytes))
            items.append(EKPO(
                ebeln=item_data["ebeln"],
                ebelp=item_data["ebelp"],
                matnr=item_data["matnr"],
                menge=item_data["menge"],
                netpr=item_data["netpr"]
            ))
            
        return EKKO(
            ebeln=header_data["ebeln"],
            lifnr=header_data["lifnr"],
            bedat=datetime.fromisoformat(header_data["bedat"]),
            items=items,
            status=header_data["status"]
        )

    def save_material_document(self, mkpf: MKPF) -> None:
        """Persist Material Document (MKPF/MSEG) to Kotoba KQE and publish to KSE."""
        mblnr_subject = f"mkpf:{mkpf.mblnr}"
        
        header_data = {
            "mblnr": mkpf.mblnr,
            "budat": mkpf.budat.isoformat(),
            "usnam": mkpf.usnam,
            "status": mkpf.status
        }
        
        kqe.assert_quad(Quad(
            graph=self.graph_name,
            subject=mblnr_subject,
            predicate="erp:mm:mkpf_header",
            object_cbor=list(cbor2.dumps(header_data))
        ))

        total_value = 0.0
        mock_price = 10.50 # Real system fetches standard price from MARA/MBEW

        for item in mkpf.items:
            item_data = {
                "mblnr": item.mblnr,
                "zeile": item.zeile,
                "bwart": item.bwart,
                "matnr": item.matnr,
                "menge": item.menge,
                "ebeln": item.ebeln,
                "ebelp": item.ebelp
            }
            total_value += item.menge * mock_price

            kqe.assert_quad(Quad(
                graph=self.graph_name,
                subject=mblnr_subject,
                predicate="erp:mm:mseg_item",
                object_cbor=list(cbor2.dumps(item_data))
            ))
            
        # Publish an event to the stream engine for the FI module
        # Using SAP standard terminology (Goods Receipt -> WE / Material Document)
        event_payload = {
            "event_type": "GoodsReceiptPosted",
            "mblnr": mkpf.mblnr,
            "ebeln": mkpf.items[0].ebeln if mkpf.items else "",
            "total_value": total_value,
            "timestamp": mkpf.budat.isoformat()
        }
        kse.publish("erp.mm.mkpf", list(cbor2.dumps(event_payload)))
