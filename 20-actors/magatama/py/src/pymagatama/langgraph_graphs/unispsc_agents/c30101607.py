from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class MagnesiumState(TypedDict):
    specs: dict
    validated: bool
    safety_clearance: bool

def validate_composition(state: MagnesiumState):
    state['validated'] = state['specs'].get('purity_percent', 0) >= 99.9
    return state

def check_hazmat_compliance(state: MagnesiumState):
    state['safety_clearance'] = True
    return state

graph = StateGraph(MagnesiumState)
graph.add_node('validate', validate_composition)
graph.add_node('safety', check_hazmat_compliance)
graph.add_edge('validate', 'safety')
graph.add_edge('safety', END)
graph.set_entry_point('validate')
graph = graph.compile()