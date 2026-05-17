from typing import TypedDict
from langgraph.graph import StateGraph, END

class PinState(TypedDict):
    material: str
    length: float
    inspection_passed: bool

def validate_material(state: PinState):
    state['inspection_passed'] = state['material'] in ['Stainless Steel', 'Nickel Plated Steel']
    return state

def check_dimensions(state: PinState):
    if state['length'] < 10.0 or state['length'] > 100.0:
        state['inspection_passed'] = False
    return state

workflow = StateGraph(PinState)
workflow.add_node('validate_material', validate_material)
workflow.add_node('check_dimensions', check_dimensions)
workflow.add_edge('validate_material', 'check_dimensions')
workflow.add_edge('check_dimensions', END)
workflow.set_entry_point('validate_material')
graph = workflow.compile()