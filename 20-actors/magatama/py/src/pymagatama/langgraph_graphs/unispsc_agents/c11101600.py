from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class GasProcurementState(TypedDict):
    purity_level: float
    cylinder_type: str
    compliance_checks: List[str]
    is_approved: bool

def validate_safety(state: GasProcurementState) -> GasProcurementState:
    # Logic to verify dangerous goods handling
    state['compliance_checks'].append('Safety Protocol Verified')
    return state

def check_purity(state: GasProcurementState) -> GasProcurementState:
    if state['purity_level'] >= 99.9:
        state['is_approved'] = True
    return state

graph = StateGraph(GasProcurementState)
graph.add_node('safety_check', validate_safety)
graph.add_node('purity_analysis', check_purity)
graph.set_entry_point('safety_check')
graph.add_edge('safety_check', 'purity_analysis')
graph.add_edge('purity_analysis', END)
graph = graph.compile()
