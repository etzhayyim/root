from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class MetalPowderState(TypedDict):
    purity: float
    particle_size_d50: float
    is_certified: bool
    compliance_risk: List[str]

def validate_purity(state: MetalPowderState):
    state['is_certified'] = state['purity'] >= 99.9
    return state

def check_compliance(state: MetalPowderState):
    if not state['is_certified']:
        state['compliance_risk'].append('Low Purity Risk')
    return state

graph = StateGraph(MetalPowderState)
graph.add_node('validate_purity', validate_purity)
graph.add_node('check_compliance', check_compliance)
graph.set_entry_point('validate_purity')
graph.add_edge('validate_purity', 'check_compliance')
graph.add_edge('check_compliance', END)
graph = graph.compile()