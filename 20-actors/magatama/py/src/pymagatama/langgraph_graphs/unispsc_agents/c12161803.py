from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class MetalPowderState(TypedDict):
    powder_id: str
    purity: float
    particle_size: float
    is_approved: bool
    logs: List[str]

def validate_powder(state: MetalPowderState) -> MetalPowderState:
    if state['purity'] >= 99.9 and state['particle_size'] < 50.0:
        state['is_approved'] = True
        state['logs'].append('Validation successful: High purity and fine size.')
    else:
        state['is_approved'] = False
        state['logs'].append('Validation failed: Purity or size out of specs.')
    return state

def route_by_validation(state: MetalPowderState) -> str:
    return 'approved' if state['is_approved'] else 'rejected'

graph = StateGraph(MetalPowderState)
graph.add_node('validate', validate_powder)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
graph = graph.compile()
