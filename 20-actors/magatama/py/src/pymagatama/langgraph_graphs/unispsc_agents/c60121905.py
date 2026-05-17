from typing import TypedDict
from langgraph.graph import StateGraph, END

class CanvasState(TypedDict):
    material_spec: dict
    validation_result: bool
    approved: bool

def validate_material(state: CanvasState):
    gsm = state['material_spec'].get('gsm', 0)
    state['validation_result'] = 250 <= gsm <= 500
    return state

def check_compliance(state: CanvasState):
    state['approved'] = state['validation_result'] and state['material_spec'].get('fire_rated', False)
    return state

graph = StateGraph(CanvasState)
graph.add_node('validate', validate_material)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()