from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class MetalSpecState(TypedDict):
    material_code: str
    purity_level: float
    inspection_passed: bool
    compliance_report: List[str]

def validate_alloy_composition(state: MetalSpecState) -> MetalSpecState:
    if state['purity_level'] >= 99.9:
        state['inspection_passed'] = True
        state['compliance_report'].append('Purity check passed')
    else:
        state['inspection_passed'] = False
        state['compliance_report'].append('Purity check failed')
    return state

def approve_procurement(state: MetalSpecState) -> MetalSpecState:
    if state['inspection_passed']:
        state['compliance_report'].append('Procurement approved')
    return state

graph = StateGraph(MetalSpecState)
graph.add_node('validate', validate_alloy_composition)
graph.add_node('approve', approve_procurement)
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph.set_entry_point('validate')
graph = graph.compile()
