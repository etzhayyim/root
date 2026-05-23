from typing import TypedDict
from langgraph.graph import StateGraph, END

class ForgingState(TypedDict):
    part_specs: dict
    validation_passed: bool

def validate_geometry(state: ForgingState):
    # Simulate CAD geometry validation logic
    state['validation_passed'] = 'tolerance' in state['part_specs']
    return state

def check_material_cert(state: ForgingState):
    # logic to verify metallurgical certification
    return {'validation_passed': state['validation_passed'] and 'cert' in state['part_specs']}

graph = StateGraph(ForgingState)
graph.add_node('validate_geometry', validate_geometry)
graph.add_node('check_material_cert', check_material_cert)
graph.add_edge('validate_geometry', 'check_material_cert')
graph.add_edge('check_material_cert', END)
graph.set_entry_point('validate_geometry')
graph = graph.compile()
