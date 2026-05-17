from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class GarmentState(TypedDict):
    material_specs: dict
    safety_compliance: bool
    approved: bool

def validate_materials(state: GarmentState):
    # Simulate material check for children's clothing
    state['safety_compliance'] = all(value is not None for value in state['material_specs'].values())
    return state

def check_compliance(state: GarmentState):
    state['approved'] = state['safety_compliance']
    return 'end'

graph = StateGraph(GarmentState)
graph.add_node('validate', validate_materials)
graph.add_node('compliance', check_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()