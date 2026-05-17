import operator
from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, END

class BeanProcurementState(TypedDict):
    order_details: dict
    compliance_check: bool
    final_report: str

def validate_shelf_life(state: BeanProcurementState):
    expiry = state['order_details'].get('expiry_date')
    is_compliant = expiry is not None and len(expiry) > 0
    return {'compliance_check': is_compliant}

def generate_procurement_report(state: BeanProcurementState):
    status = 'APPROVED' if state['compliance_check'] else 'REJECTED'
    return {'final_report': f'Procurement status for batch: {status}'}

graph = StateGraph(BeanProcurementState)
graph.add_node('validate_shelf_life', validate_shelf_life)
graph.add_node('generate_procurement_report', generate_procurement_report)
graph.set_entry_point('validate_shelf_life')
graph.add_edge('validate_shelf_life', 'generate_procurement_report')
graph.add_edge('generate_procurement_report', END)
app = graph.compile()