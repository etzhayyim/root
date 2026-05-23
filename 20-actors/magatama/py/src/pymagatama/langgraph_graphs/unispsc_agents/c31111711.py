from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class ExtrusionState(TypedDict):
    material_purity: float
    specs_verified: bool
    traceability_logs: List[str]

def validate_material(state: ExtrusionState):
    state['specs_verified'] = state['material_purity'] >= 99.9
    return state

def check_compliance(state: ExtrusionState):
    if state['specs_verified']:
        state['traceability_logs'].append('Compliance Verified')
    return state

graph = StateGraph(ExtrusionState)
graph.add_node('validate', validate_material)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
