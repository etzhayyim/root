from typing import TypedDict
from langgraph.graph import StateGraph, END

class FoilState(TypedDict):
    purity: float
    thickness: float
    status: str

def validate_physics(state: FoilState):
    if state['purity'] < 99.0:
        return {'status': 'rejected_purity'}
    return {'status': 'validated'}

def structural_check(state: FoilState):
    if state['thickness'] < 0.01:
        return {'status': 'rejected_too_thin'}
    return {'status': 'approved'}

graph = StateGraph(FoilState)
graph.add_node('validate', validate_physics)
graph.add_node('structure', structural_check)
graph.add_edge('validate', 'structure')
graph.add_edge('structure', END)
graph.set_entry_point('validate')
graph = graph.compile()