from typing import TypedDict
from langgraph.graph import StateGraph, END

class BathroomWallState(TypedDict):
    spec_data: dict
    validation_passed: bool
    compliance_report: str

def validate_materials(state: BathroomWallState):
    required = ['waterproof_rating', 'material_composition']
    passed = all(k in state['spec_data'] for k in required)
    return {'validation_passed': passed, 'compliance_report': 'Validated physical specs' if passed else 'Missing data'}

def check_fire_safety(state: BathroomWallState):
    return {'compliance_report': state['compliance_report'] + ', Fire safety check complete.'}

graph = StateGraph(BathroomWallState)
graph.add_node('validate', validate_materials)
graph.add_node('safety', check_fire_safety)
graph.set_entry_point('validate')
graph.add_edge('validate', 'safety')
graph.add_edge('safety', END)
graph = graph.compile()