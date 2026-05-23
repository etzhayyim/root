from typing import TypedDict
from langgraph.graph import StateGraph, END

class RescueLoopState(TypedDict):
    tensile_strength: float
    certification: str
    is_compliant: bool

def validate_specs(state: RescueLoopState):
    state['is_compliant'] = state['tensile_strength'] >= 22.0 and state['certification'] in ['NFPA', 'EN']
    return state

graph = StateGraph(RescueLoopState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
compile_graph = graph.compile()
