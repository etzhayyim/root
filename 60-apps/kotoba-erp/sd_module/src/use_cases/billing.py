from typing import TypedDict, List
import datetime
from src.domain.entities import VBRK, VBRP, VBAK
from src.adapters.repository import SDRepository

class GenerateBillingState(TypedDict):
    input_data: dict
    vbrk: VBRK | None
    vbak: VBAK | None
    errors: List[str]
    status: str

def parse_billing_request(state: GenerateBillingState) -> dict:
    data = state["input_data"]
    order_id = data.get("order_id", "") # References VBAK vbeln
    
    vbrk = VBRK(
        vbeln=data.get("billing_id", "INV-TEMP"),
        fkart="F2", # Invoice
        kunnr="", # To be filled from VBAK
        fkdat=datetime.datetime.now(),
        netwr=0.0,
        items=[]
    )
    return {"vbrk": vbrk}

def fetch_sales_order(state: GenerateBillingState) -> dict:
    repo = SDRepository()
    # input_data.order_id is passed as the parameter
    vbak = repo.get_sales_order(state["input_data"].get("order_id", ""))
    errors = state.get("errors", [])
    if not vbak:
        errors.append("Sales Order (VBAK) not found.")
    return {"vbak": vbak, "errors": errors}

def check_so_exists(state: GenerateBillingState) -> str:
    if len(state.get("errors", [])) > 0:
        return "reject"
    return "generate_lines"

def generate_lines(state: GenerateBillingState) -> dict:
    vbrk: VBRK = state["vbrk"]
    vbak: VBAK = state["vbak"]
    
    vbrk.kunnr = vbak.kunnr
    
    lines = []
    total = 0.0
    for idx, vbap in enumerate(vbak.items):
        line_total = vbap.kwmeng * vbap.netpr
        lines.append(VBRP(
            vbeln=vbrk.vbeln,
            posnr=str((idx + 1) * 10), # standard SAP step 10, 20...
            aubel=vbak.vbeln,
            aupos=vbap.posnr,
            matnr=vbap.matnr,
            fkimg=vbap.kwmeng,
            netwr=line_total
        ))
        total += line_total
        
    vbrk.items = lines
    vbrk.netwr = total
    
    return {"vbrk": vbrk}

def validate_billing(state: GenerateBillingState) -> dict:
    vbrk: VBRK = state["vbrk"]
    errors = state.get("errors", [])
    
    if not vbrk.validate_totals():
        errors.append("Billing Document (VBRK) totals do not match line items.")
        
    return {"errors": errors}

def check_validation(state: GenerateBillingState) -> str:
    if len(state.get("errors", [])) > 0:
        return "reject"
    return "post"

def post_billing(state: GenerateBillingState) -> dict:
    vbrk: VBRK = state["vbrk"]
    vbrk.status = "POSTED"
    
    repo = SDRepository()
    repo.save_billing_document(vbrk)
    
    return {"vbrk": vbrk, "status": "POSTED"}

def reject_billing(state: GenerateBillingState) -> dict:
    vbrk: VBRK = state["vbrk"]
    vbrk.status = "REJECTED"
    return {"vbrk": vbrk, "status": "REJECTED"}
