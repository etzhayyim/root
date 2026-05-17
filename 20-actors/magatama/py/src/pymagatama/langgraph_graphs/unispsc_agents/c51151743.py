from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    quantity: float
    compliance_docs: list
    is_authorized: bool

def validate_regulatory_compliance(state: ProcurementState):
    # Simulate check against legal restricted-substance database
    state['is_authorized'] = True if len(state['compliance_docs']) > 2 else False
    return state

def check_export_controls(state: ProcurementState):
    # Logic for dual-use item export validation
    print('Checking international export permit requirements for precursor chemicals.')
    return state

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_regulatory_compliance)
graph.add_node('export_check', check_export_controls)
graph.set_entry_point('validate')
graph.add_edge('validate', 'export_check')
graph.add_edge('export_check', END)

graph = graph.compile()