from typing import TypedDict
from langgraph.graph import StateGraph, END

class ToyProcurementState(TypedDict):
    product_id: str
    compliance_docs: list[str]
    status: str

def validate_safety_certs(state: ToyProcurementState):
    # Simulate verification of EN71 or ASTM F963 compliance
    state['status'] = 'CERTIFIED' if 'ST_CERT' in state['compliance_docs'] else 'PENDING'
    return state

def check_toxicity(state: ToyProcurementState):
    # Simulate material toxicity validation
    if state.get('status') == 'CERTIFIED':
        state['status'] = 'APPROVED'
    return state

graph = StateGraph(ToyProcurementState)
graph.add_node('safety', validate_safety_certs)
graph.add_node('toxicity', check_toxicity)
graph.set_entry_point('safety')
graph.add_edge('safety', 'toxicity')
graph.add_edge('toxicity', END)
graph = graph.compile()
