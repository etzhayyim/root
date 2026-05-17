from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class NanopowderState(TypedDict):
    material_id: str
    purity_check: bool
    safety_clearance: bool
    steps: List[str]

def validate_purity(state: NanopowderState):
    # Simulate ICP-MS or XRD purity validation logic
    state['purity_check'] = True
    state['steps'].append('Purity validated by spectral analysis')
    return state

def check_safety_protocols(state: NanopowderState):
    # Verify dual-use export and handling safety
    state['safety_clearance'] = True
    state['steps'].append('Safety handling protocols verified')
    return state

graph = StateGraph(NanopowderState)
graph.add_node('validate', validate_purity)
graph.add_node('safety', check_safety_protocols)
graph.add_edge('validate', 'safety')
graph.add_edge('safety', END)
graph.set_entry_point('validate')
graph = graph.compile()