from typing import TypedDict
from langgraph.graph import StateGraph, END

class MatState(TypedDict):
    specs: dict
    approved: bool

def validate_dimensions(state: MatState):
    width = state['specs'].get('width', 0)
    length = state['specs'].get('length', 0)
    state['approved'] = width > 0 and length > 0
    return state

def check_compliance(state: MatState):
    state['approved'] = state['approved'] and state['specs'].get('fire_rated', False)
    return state

graph = StateGraph(MatState)
graph.add_node('validate', validate_dimensions)
graph.add_node('compliance', check_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
mat_workflow = graph.compile()