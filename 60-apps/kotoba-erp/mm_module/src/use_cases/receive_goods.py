from typing import TypedDict, List
import datetime
from src.domain.entities import MKPF, MSEG, EKKO
from src.adapters.repository import MMRepository

class ReceiveGoodsState(TypedDict):
    input_data: dict
    mkpf: MKPF | None
    ekko: EKKO | None
    errors: List[str]
    status: str

def parse_receipt(state: ReceiveGoodsState) -> dict:
    data = state["input_data"]
    items = []
    
    # Expected payload: mblnr, ebeln, items: [{matnr, menge, ebelp}]
    mblnr = data.get("mblnr", "GR-TEMP")
    ebeln = data.get("ebeln", "")
    
    for idx, l in enumerate(data.get("items", [])):
        items.append(MSEG(
            mblnr=mblnr,
            zeile=str(idx + 1),
            bwart="101",
            matnr=l["matnr"],
            menge=float(l["menge"]),
            ebeln=ebeln,
            ebelp=l.get("ebelp", "10")
        ))
    
    mkpf = MKPF(
        mblnr=mblnr,
        budat=datetime.datetime.now(),
        usnam=data.get("usnam", "SYSTEM"),
        items=items
    )
    return {"mkpf": mkpf}

def fetch_po(state: ReceiveGoodsState) -> dict:
    repo = MMRepository()
    # In a real system, we'd get ebeln from the first MSEG item or payload root
    ebeln = state["mkpf"].items[0].ebeln if state["mkpf"].items else ""
    ekko = repo.get_purchase_order(ebeln)
    errors = state.get("errors", [])
    if not ekko:
        errors.append("Purchase Order (EKKO) not found.")
    return {"ekko": ekko, "errors": errors}

def check_po_exists(state: ReceiveGoodsState) -> str:
    if len(state.get("errors", [])) > 0:
        return "reject"
    return "validate"

def validate_receipt(state: ReceiveGoodsState) -> dict:
    mkpf: MKPF = state["mkpf"]
    ekko: EKKO = state["ekko"]
    errors = state.get("errors", [])
    
    if not mkpf.validate_receipt(ekko):
        errors.append("Material Document invalid against PO (EKKO) (e.g. quantity exceeded).")
        
    return {"errors": errors}

def check_validation(state: ReceiveGoodsState) -> str:
    if len(state.get("errors", [])) > 0:
        return "reject"
    return "post"

def post_receipt(state: ReceiveGoodsState) -> dict:
    mkpf: MKPF = state["mkpf"]
    mkpf.status = "POSTED"
    
    repo = MMRepository()
    repo.save_material_document(mkpf)
    
    return {"mkpf": mkpf, "status": "POSTED"}

def reject_receipt(state: ReceiveGoodsState) -> dict:
    mkpf: MKPF = state["mkpf"]
    mkpf.status = "REJECTED"
    return {"mkpf": mkpf, "status": "REJECTED"}
