from typing import TypedDict
from langgraph.graph import StateGraph, END

class VProcessState(TypedDict):
    specs: dict
    validation_score: float
    approved: bool

def validate_specs(state: VProcessState):
    # Perform dimensional and metallurgical validation logic
    state['validation_score'] = 0.95 if 'alloy' in state['specs'] else 0.0
    return state

def check_quality(state: VProcessState):
    state['approved'] = state['validation_score'] > 0.9
    return state

graph = StateGraph(VProcessState)
graph.add_node('validate', validate_specs)
graph.add_node('quality_check', check_quality)
graph.add_edge('validate', 'quality_check')
graph.add_edge('quality_check', END)
graph.set_entry_point('validate')
graph = graph.compile()