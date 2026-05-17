from typing import TypedDict
from langgraph.graph import StateGraph, END

class ValveState(TypedDict):
    spec_data: dict
    validation_passed: bool
    error_log: list

def validate_pressure_rating(state: ValveState):
    rating = state['spec_data'].get('pressure_rating', 0)
    passed = rating > 0
    return {'validation_passed': passed, 'error_log': [] if passed else ['Invalid pressure rating']}

def check_material_safety(state: ValveState):
    if state['spec_data'].get('body_material') == 'unknown':
        return {'validation_passed': False, 'error_log': ['Material safety non-compliant']}
    return {'validation_passed': True}

graph = StateGraph(ValveState)
graph.add_node('validate_pressure', validate_pressure_rating)
graph.add_node('check_material', check_material_safety)
graph.set_entry_point('validate_pressure')
graph.add_edge('validate_pressure', 'check_material')
graph.add_edge('check_material', END)
graph = graph.compile()