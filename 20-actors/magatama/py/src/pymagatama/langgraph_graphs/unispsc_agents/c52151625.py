from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class BiscuitCutterState(TypedDict):
    material: str
    dimensions: dict
    compliance_docs: List[str]
    is_approved: bool

def validate_material(state: BiscuitCutterState):
    state['is_approved'] = state['material'] in ['Stainless Steel 304', 'Food-Grade Silicone']
    return state

def check_dimensions(state: BiscuitCutterState):
    if state['is_approved'] and 'diameter' in state['dimensions']:
        state['is_approved'] = 20 <= state['dimensions']['diameter'] <= 150
    return state

graph = StateGraph(BiscuitCutterState)
graph.add_node('validate_mat', validate_material)
graph.add_node('validate_dim', check_dimensions)
graph.set_entry_point('validate_mat')
graph.add_edge('validate_mat', 'validate_dim')
graph.add_edge('validate_dim', END)
graph = graph.compile()
