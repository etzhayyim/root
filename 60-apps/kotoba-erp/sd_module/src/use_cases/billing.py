from typing import TypedDict, List
import datetime
from src.domain.entities import BillingDocument, BillingDocumentLine, SalesOrder
from src.adapters.repository import SDRepository

class GenerateBillingState(TypedDict):
    input_data: dict
    billing_doc: BillingDocument | None
    so: SalesOrder | None
    errors: List[str]
    status: str

def parse_billing_request(state: GenerateBillingState) -> dict:
    data = state["input_data"]
    order_id = data.get("order_id", "")
    
    # We will construct the lines from the sales order later
    # Just initialize the document stub
    billing_doc = BillingDocument(
        billing_id=data.get("billing_id", "INV-TEMP"),
        order_id=order_id,
        customer_id="", # to be filled from SO
        date=datetime.datetime.now(),
        lines=[],
        total_amount=0.0
    )
    return {"billing_doc": billing_doc}

def fetch_sales_order(state: GenerateBillingState) -> dict:
    repo = SDRepository()
    so = repo.get_sales_order(state["billing_doc"].order_id)
    errors = state.get("errors", [])
    if not so:
        errors.append("Sales Order not found.")
    return {"so": so, "errors": errors}

def check_so_exists(state: GenerateBillingState) -> str:
    if len(state.get("errors", [])) > 0:
        return "reject"
    return "generate_lines"

def generate_lines(state: GenerateBillingState) -> dict:
    billing_doc: BillingDocument = state["billing_doc"]
    so: SalesOrder = state["so"]
    
    billing_doc.customer_id = so.customer_id
    
    lines = []
    total = 0.0
    for so_line in so.lines:
        line_total = so_line.quantity * so_line.unit_price
        lines.append(BillingDocumentLine(
            material_id=so_line.material_id,
            quantity=so_line.quantity,
            unit_price=so_line.unit_price,
            line_total=line_total
        ))
        total += line_total
        
    billing_doc.lines = lines
    billing_doc.total_amount = total
    
    return {"billing_doc": billing_doc}

def validate_billing(state: GenerateBillingState) -> dict:
    billing_doc: BillingDocument = state["billing_doc"]
    errors = state.get("errors", [])
    
    if not billing_doc.validate_totals():
        errors.append("Billing Document totals do not match line items.")
        
    return {"errors": errors}

def check_validation(state: GenerateBillingState) -> str:
    if len(state.get("errors", [])) > 0:
        return "reject"
    return "post"

def post_billing(state: GenerateBillingState) -> dict:
    billing_doc: BillingDocument = state["billing_doc"]
    billing_doc.status = "POSTED"
    
    repo = SDRepository()
    repo.save_billing_document(billing_doc)
    
    return {"billing_doc": billing_doc, "status": "POSTED"}

def reject_billing(state: GenerateBillingState) -> dict:
    billing_doc: BillingDocument = state["billing_doc"]
    billing_doc.status = "REJECTED"
    return {"billing_doc": billing_doc, "status": "REJECTED"}
