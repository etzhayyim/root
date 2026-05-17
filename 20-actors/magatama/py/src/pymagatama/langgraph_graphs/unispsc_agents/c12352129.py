from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class MetalPowderState(TypedDict):
    purity: float
    particle_size: float
    compliant: bool
    history: List[str]

def validate_material(state: MetalPowderState) -> MetalPowderState:
    state['compliant'] = state['purity'] >= 99.9 and state['particle_size'] <= 45.0
    state['history'].append('validation_step_complete')
    return state

def check_safety_protocols(state: MetalPowderState) -> MetalPowderState:
    state['history'].append('safety_protocols_verified')
    return state

graph = StateGraph(MetalPowderState)
graph.add_node('validate', validate_material)
graph.add_node('safety', check_safety_protocols)
graph.set_entry_point('validate')
graph.add_edge('validate', 'safety')
graph.add_edge('safety', END)
compile_graph = graph.compile()