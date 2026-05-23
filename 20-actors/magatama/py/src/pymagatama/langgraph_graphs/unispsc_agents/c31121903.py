from typing import TypedDict
from langgraph.graph import StateGraph, END

class MoldState(TypedDict):
    dimensions: dict
    material_grade: str
    is_compliant: bool

def validate_specs(state: MoldState):
    # Perform dimensional validation logic
    state['is_compliant'] = all(val > 0 for val in state['dimensions'].values())
    return state

def check_material(state: MoldState):
    # Verify dual-use export control status based on material grade
    state['is_compliant'] = state['is_compliant'] and state['material_grade'] != 'restricted'
    return state

graph = StateGraph(MoldState)
graph.add_node('validate', validate_specs)
graph.add_node('material_check', check_material)
graph.set_entry_point('validate')
graph.add_edge('validate', 'material_check')
graph.add_edge('material_check', END)
graph = graph.compile()
