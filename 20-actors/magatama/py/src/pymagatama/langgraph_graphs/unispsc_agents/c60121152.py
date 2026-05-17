from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class SlateState(TypedDict):
    material: str
    dimensions: tuple
    status: str

def validate_material(state: SlateState):
    allowed = ['slate rock', 'polymer', 'coated steel']
    return {'status': 'validated' if state['material'] in allowed else 'rejected'}

def check_dimensions(state: SlateState):
    return {'status': 'ready_for_procurement' if all(d > 0 for d in state['dimensions']) else 'error'}

graph = StateGraph(SlateState)
graph.add_node('validate', validate_material)
graph.add_node('dimension_check', check_dimensions)
graph.set_entry_point('validate')
graph.add_edge('validate', 'dimension_check')
graph.add_edge('dimension_check', END)
graph = graph.compile()