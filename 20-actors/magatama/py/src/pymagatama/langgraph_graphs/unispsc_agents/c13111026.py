from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class NickelState(TypedDict):
    purity_level: float
    trace_elements: List[str]
    certification_verified: bool
    compliance_risk: str

def validate_purity(state: NickelState) -> NickelState:
    if state['purity_level'] < 99.0:
        state['compliance_risk'] = 'CRITICAL_IMPURITY'
    return state

def check_certification(state: NickelState) -> NickelState:
    state['certification_verified'] = True
    return state

graph = StateGraph(NickelState)
graph.add_node('validate', validate_purity)
graph.add_node('certify', check_certification)
graph.add_edge('validate', 'certify')
graph.add_edge('certify', END)
graph.set_entry_point('validate')
compiled_graph = graph.compile()
