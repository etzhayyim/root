from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class ResinProcessingState(TypedDict):
    material_id: str
    purity_level: float
    specs_validated: bool
    compliance_cleared: bool

def validate_purity(state: ResinProcessingState):
    is_pure = state['purity_level'] >= 0.99
    return {'specs_validated': is_pure}

def check_compliance(state: ResinProcessingState):
    is_compliant = state.get('specs_validated', False)
    return {'compliance_cleared': is_compliant}

graph = StateGraph(ResinProcessingState)
graph.add_node('validate_purity', validate_purity)
graph.add_node('check_compliance', check_compliance)
graph.set_entry_point('validate_purity')
graph.add_edge('validate_purity', 'check_compliance')
graph.add_edge('check_compliance', END)
graph = graph.compile()
