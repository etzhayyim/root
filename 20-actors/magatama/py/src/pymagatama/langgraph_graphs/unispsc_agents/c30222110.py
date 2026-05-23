from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class CoastguardProjectState(TypedDict):
    project_id: str
    security_clearance: bool
    structural_specs: List[str]
    approved: bool

def validate_clearance(state: CoastguardProjectState):
    state['security_clearance'] = True
    return state

def validate_specs(state: CoastguardProjectState):
    state['approved'] = len(state['structural_specs']) > 0
    return state

graph = StateGraph(CoastguardProjectState)
graph.add_node('clearance_check', validate_clearance)
graph.add_node('spec_validation', validate_specs)
graph.set_entry_point('clearance_check')
graph.add_edge('clearance_check', 'spec_validation')
graph.add_edge('spec_validation', END)
graph = graph.compile()
