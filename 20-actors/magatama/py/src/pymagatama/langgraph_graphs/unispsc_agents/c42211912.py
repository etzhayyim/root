from langgraph.graph import StateGraph, END
from typing import TypedDict

class ProcurementState(TypedDict):
    device_specs: dict
    validation_passed: bool

def validate_ergonomics(state: ProcurementState):
    # Simulate validation logic for accessibility standards
    state['validation_passed'] = state['device_specs'].get('ergonomic_rating') >= 4
    return 'validate_ergonomics'

def check_material_safety(state: ProcurementState):
    return {'validation_passed': state['device_specs'].get('food_grade', False)}

graph = StateGraph(ProcurementState)
graph.add_node('ergonomics', validate_ergonomics)
graph.add_node('safety', check_material_safety)
graph.set_entry_point('ergonomics')
graph.add_edge('ergonomics', 'safety')
graph.add_edge('safety', END)
app = graph.compile()
