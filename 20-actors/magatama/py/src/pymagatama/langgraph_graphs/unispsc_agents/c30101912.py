from typing import TypedDict
from langgraph.graph import StateGraph, END

class ZincState(TypedDict):
    purity: float
    weight: float
    is_compliant: bool

def validate_purity(state: ZincState):
    state['is_compliant'] = state['purity'] >= 99.9
    return state

def check_dimensions(state: ZincState):
    # Simulate CAD/Dimension validation logic
    return {'is_compliant': state['is_compliant'] and state['weight'] > 0}

graph = StateGraph(ZincState)
graph.add_node('validate', validate_purity)
graph.add_node('dimension_check', check_dimensions)
graph.add_edge('validate', 'dimension_check')
graph.add_edge('dimension_check', END)
graph.set_entry_point('validate')
graph = graph.compile()