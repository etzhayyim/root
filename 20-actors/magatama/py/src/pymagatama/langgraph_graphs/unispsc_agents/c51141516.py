from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    product_name: str
    batch_id: str
    is_gdp_compliant: bool

def validate_gdp(state: ProcurementState):
    return {'is_gdp_compliant': True if state['batch_id'] else False}

def process_shipment(state: ProcurementState):
    return {'status': 'Validated' if state['is_gdp_compliant'] else 'Rejected'}

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_gdp)
graph.add_node('ship', process_shipment)
graph.set_entry_point('validate')
graph.add_edge('validate', 'ship')
graph.add_edge('ship', END)
graph = graph.compile()