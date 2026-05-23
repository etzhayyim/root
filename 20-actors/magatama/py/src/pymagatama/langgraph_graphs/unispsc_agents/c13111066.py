from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class MetalIngotState(TypedDict):
    batch_id: str
    purity_level: float
    inspection_status: bool
    compliance_tags: List[str]

def validate_purity(state: MetalIngotState) -> MetalIngotState:
    if state['purity_level'] >= 0.999:
        state['inspection_status'] = True
        state['compliance_tags'].append('high-grade-verified')
    else:
        state['inspection_status'] = False
    return state

def route_by_purity(state: MetalIngotState) -> str:
    return 'validate' if state.get('purity_level') else END

builder = StateGraph(MetalIngotState)
builder.add_node('validate', validate_purity)
builder.set_entry_point('validate')
builder.add_edge('validate', END)
graph = builder.compile()
