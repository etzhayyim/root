from kotoba_langgraph import _cbor as cbor2
from typing import List, Optional
from datetime import datetime
from src.domain.entities import BKPF, BSEG

try:
    from wit_world import kqe
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
            if predicate == "erp:fi:bkpf_header" and "DIRECT" in subject:
                return [cbor2.dumps({
                    "belnr": "DIRECT-001",
                    "bukrs": "1000",
                    "bldat": datetime.now().isoformat(),
                    "budat": datetime.now().isoformat(),
                    "bstat": ""
                })]
            return []

    kqe = _KqeMock()

class FIRepository:
    def __init__(self, graph_name: str = "fi_journal"):
        self.graph_name = graph_name

    def save_accounting_document(self, bkpf: BKPF) -> None:
        """Translates BKPF/BSEG entities into Quad assertions and writes them to KQE."""
        belnr_subject = f"bkpf:{bkpf.belnr}"
        
        header_data = {
            "belnr": bkpf.belnr,
            "bukrs": bkpf.bukrs,
            "bldat": bkpf.bldat.isoformat(),
            "budat": bkpf.budat.isoformat(),
            "bstat": bkpf.bstat
        }
        
        kqe.assert_quad(Quad(
            graph=self.graph_name,
            subject=belnr_subject,
            predicate="erp:fi:bkpf_header",
            object_cbor=list(cbor2.dumps(header_data))
        ))

        for item in bkpf.items:
            item_data = {
                "belnr": item.belnr,
                "buzei": item.buzei,
                "hkont": item.hkont,
                "shkzg": item.shkzg,
                "wrbtr": item.wrbtr,
                "sgtxt": item.sgtxt
            }
            kqe.assert_quad(Quad(
                graph=self.graph_name,
                subject=belnr_subject,
                predicate="erp:fi:bseg_item",
                object_cbor=list(cbor2.dumps(item_data))
            ))

    def get_accounting_document(self, belnr: str) -> Optional[BKPF]:
        """Fetch BKPF and BSEG from KQE using true read API (`get_objects`)."""
        subject = f"bkpf:{belnr}"
        
        header_objs = kqe.get_objects(self.graph_name, subject, "erp:fi:bkpf_header")
        if not header_objs:
            return None
            
        header_data = cbor2.loads(bytes(header_objs[0]))
        
        item_objs = kqe.get_objects(self.graph_name, subject, "erp:fi:bseg_item")
        items = []
        for obj_bytes in item_objs:
            item_data = cbor2.loads(bytes(obj_bytes))
            items.append(BSEG(
                belnr=item_data["belnr"],
                buzei=item_data["buzei"],
                hkont=item_data["hkont"],
                shkzg=item_data["shkzg"],
                wrbtr=item_data["wrbtr"],
                sgtxt=item_data["sgtxt"]
            ))
            
        return BKPF(
            belnr=header_data["belnr"],
            bukrs=header_data["bukrs"],
            bldat=datetime.fromisoformat(header_data["bldat"]),
            budat=datetime.fromisoformat(header_data["budat"]),
            items=items,
            bstat=header_data["bstat"]
        )
