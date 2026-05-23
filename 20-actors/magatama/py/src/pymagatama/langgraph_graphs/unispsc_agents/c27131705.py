from typing import TypedDict
from langgraph.graph import StateGraph, END

class CylinderState(TypedDict):
    spec_data: dict
    validation_passed: bool
    error_log: list

def validate_specs(state: CylinderState):
    required = ['material_grade', 'inner_diameter_tolerance']
    passed = all(k in state['spec_data'] for k in required)
    return {'validation_passed': passed, 'error_log': [] if passed else ['Missing mandatory fields']}

def check_compliance(state: CylinderState):
    # Dual-use check logic
    if state['spec_data'].get('working_pressure_rating', 0) > 500:
        state['error_log'].append('High pressure rating - triggers export review')
    return state

graph = StateGraph(CylinderState)
graph.add_node('validator', validate_specs)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validator')
graph.add_edge('validator', 'compliance')
graph.add_edge('compliance', END)
graph.add_edge('compliance', END)
