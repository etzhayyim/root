from langgraph.graph import StateGraph, END
from typing import TypedDict

class ClampState(TypedDict):
    material: str
    force_rating: float
    status: str

def validate_specs(state: ClampState):
    if state['force_rating'] <= 0:
        return {'status': 'rejected'}
    return {'status': 'validated'}

def route_by_material(state: ClampState):
    if state['material'] == 'stainless':
        return 'special_coating_check'
    return 'standard_check'

graph = StateGraph(ClampState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
app = graph.compile()
