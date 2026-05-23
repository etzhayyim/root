from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class CatalystState(TypedDict):
    catalyst_id: str
    purity_check: bool
    safety_clearance: bool
    processing_steps: List[str]

def validate_purity(state: CatalystState) -> CatalystState:
    state['purity_check'] = True
    state['processing_steps'].append('Purity Verification Completed')
    return state

def check_safety(state: CatalystState) -> CatalystState:
    state['safety_clearance'] = True
    state['processing_steps'].append('Safety Compliance Check Passed')
    return state

builder = StateGraph(CatalystState)
builder.add_node('purity_node', validate_purity)
builder.add_node('safety_node', check_safety)
builder.add_edge('purity_node', 'safety_node')
builder.set_entry_point('purity_node')
builder.add_edge('safety_node', END)
graph = builder.compile()
