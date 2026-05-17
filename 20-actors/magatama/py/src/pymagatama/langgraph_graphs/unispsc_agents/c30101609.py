from typing import TypedDict
from langgraph.graph import StateGraph, END

class CopperState(TypedDict):
    purity: float
    dimensions: dict
    approved: bool

def validate_purity(state: CopperState):
    state['approved'] = state['purity'] >= 99.9
    return state

def check_dimensions(state: CopperState):
    if state['approved'] and 'diameter' in state['dimensions']:
        state['approved'] = True
    else:
        state['approved'] = False
    return state

graph = StateGraph(CopperState)
graph.add_node('validate_purity', validate_purity)
graph.add_node('check_dimensions', check_dimensions)
graph.set_entry_point('validate_purity')
graph.add_edge('validate_purity', 'check_dimensions')
graph.add_edge('check_dimensions', END)
graph = graph.compile()