from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    batch_id: str
    purity: float
    license_valid: bool
    approved: bool

def validate_compliance(state: ProcurementState) -> dict:
    is_valid = state['purity'] >= 99.0 and state['license_valid']
    return {'approved': is_valid}

def process_shipment(state: ProcurementState) -> dict:
    # Logic for cold chain validation would be injected here
    return {'approved': True}

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_compliance)
graph.add_node('ship', process_shipment)
graph.set_entry_point('validate')
graph.add_edge('validate', 'ship')
graph.add_edge('ship', END)
app = graph.compile()
