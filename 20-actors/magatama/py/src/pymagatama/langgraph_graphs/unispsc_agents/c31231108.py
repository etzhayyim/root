from typing import TypedDict
from langgraph.graph import StateGraph, END

class MagnesiumState(TypedDict):
    material_grade: str
    purity_level: float
    has_msds: bool
    is_approved: bool

def validate_specs(state: MagnesiumState):
    state['is_approved'] = state['purity_level'] >= 99.9 and state['has_msds'] is True
    return state

def route_procurement(state: MagnesiumState):
    return 'approved' if state.get('is_approved') else 'flag_for_review'

graph = StateGraph(MagnesiumState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph.compile()
