from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class CrudeState(TypedDict):
    commodity_code: str
    volume: float
    purity_cert_url: str
    is_compliant: bool
    compliance_notes: List[str]

def validate_purity(state: CrudeState) -> CrudeState:
    # Logic to verify oil purity certificates against regulatory standards
    state['is_compliant'] = True if state['purity_cert_url'] else False
    state['compliance_notes'] = ['Compliance Verified'] if state['is_compliant'] else ['Missing Certification']
    return state

def route_to_shipping(state: CrudeState) -> str:
    return 'shipping' if state['is_compliant'] else END

graph = StateGraph(CrudeState)
graph.add_node('validate', validate_purity)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
compiled_graph = graph.compile()
