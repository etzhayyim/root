from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProtractorState(TypedDict):
    spec_data: dict
    validated: bool

def validate_precision(state: ProtractorState):
    res = state['spec_data'].get('graduation_resolution', 1.0)
    state['validated'] = res <= 0.5
    return state

def check_material(state: ProtractorState):
    material = state['spec_data'].get('material', 'plastic')
    state['validated'] = state['validated'] and (material in ['stainless_steel', 'aluminum'])
    return state

graph = StateGraph(ProtractorState)
graph.add_node('validate_precision', validate_precision)
graph.add_node('check_material', check_material)
graph.set_entry_point('validate_precision')
graph.add_edge('validate_precision', 'check_material')
graph.add_edge('check_material', END)
graph = graph.compile()