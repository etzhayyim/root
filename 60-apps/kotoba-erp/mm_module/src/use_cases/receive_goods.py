from typing import TypedDict, List
import datetime
from src.domain.entities import GoodsReceipt, GoodsReceiptLine, PurchaseOrder
from src.adapters.repository import MMRepository

class ReceiveGoodsState(TypedDict):
    input_data: dict
    receipt: GoodsReceipt | None
    po: PurchaseOrder | None
    errors: List[str]
    status: str

def parse_receipt(state: ReceiveGoodsState) -> dict:
    data = state["input_data"]
    lines = []
    for l in data.get("lines", []):
        lines.append(GoodsReceiptLine(
            material_id=l["material_id"],
            received_quantity=float(l["received_quantity"])
        ))
    
    receipt = GoodsReceipt(
        receipt_id=data.get("receipt_id", "GR-TEMP"),
        po_number=data.get("po_number", ""),
        date=datetime.datetime.now(),
        lines=lines
    )
    return {"receipt": receipt}

def fetch_po(state: ReceiveGoodsState) -> dict:
    repo = MMRepository()
    po = repo.get_purchase_order(state["receipt"].po_number)
    errors = state.get("errors", [])
    if not po:
        errors.append("Purchase Order not found.")
    return {"po": po, "errors": errors}

def check_po_exists(state: ReceiveGoodsState) -> str:
    if len(state.get("errors", [])) > 0:
        return "reject"
    return "validate"

def validate_receipt(state: ReceiveGoodsState) -> dict:
    receipt: GoodsReceipt = state["receipt"]
    po: PurchaseOrder = state["po"]
    errors = state.get("errors", [])
    
    if not receipt.validate_receipt(po):
        errors.append("Goods receipt invalid against PO (e.g. quantity exceeded).")
        
    return {"errors": errors}

def check_validation(state: ReceiveGoodsState) -> str:
    if len(state.get("errors", [])) > 0:
        return "reject"
    return "post"

def post_receipt(state: ReceiveGoodsState) -> dict:
    receipt: GoodsReceipt = state["receipt"]
    receipt.status = "POSTED"
    
    repo = MMRepository()
    repo.save_goods_receipt(receipt)
    
    return {"receipt": receipt, "status": "POSTED"}

def reject_receipt(state: ReceiveGoodsState) -> dict:
    receipt: GoodsReceipt = state["receipt"]
    receipt.status = "REJECTED"
    return {"receipt": receipt, "status": "REJECTED"}
