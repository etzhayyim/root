from typing import TypedDict
from langgraph.graph import StateGraph, END

class CopperChannelState(TypedDict):
    specs: dict
    validation_results: dict

def validate_purity(state: CopperChannelState):
    purity = state['specs'].get('purity_percentage', 0)
    state['validation_results']['purity_ok'] = purity >= 99.9
    return state

def check_dimensions(state: CopperChannelState):
    tol = state['specs'].get('dimensional_tolerances_mm', 0.1)
    state['validation_results']['dim_ok'] = tol <= 0.05
    return state

graph = StateGraph(CopperChannelState)
graph.add_node('validate_purity', validate_purity)
graph.add_node('check_dimensions', check_dimensions)
graph.set_entry_point('validate_purity')
graph.add_edge('validate_purity', 'check_dimensions')
graph.add_edge('check_dimensions', END)
graph = graph.compile()