from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class MetalProcessState(TypedDict):
    material_id: str
    purity_level: float
    safety_check_passed: bool
    compliance_tags: List[str]
    steps_completed: List[str]

def validate_purity(state: MetalProcessState) -> MetalProcessState:
    if state['purity_level'] >= 0.99:
        state['steps_completed'].append('purity_validated')
    return state

def run_safety_protocol(state: MetalProcessState) -> MetalProcessState:
    state['safety_check_passed'] = True
    state['steps_completed'].append('safety_protocol_active')
    return state

builder = StateGraph(MetalProcessState)
builder.add_node('validate', validate_purity)
builder.add_node('safety', run_safety_protocol)
builder.set_entry_point('validate')
builder.add_edge('validate', 'safety')
builder.add_edge('safety', END)
graph = builder.compile()