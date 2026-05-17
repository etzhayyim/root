from typing import TypedDict
from langgraph.graph import StateGraph, END

class HeatingWireState(TypedDict):
    specs: dict
    validation_errors: list
    is_compliant: bool

def validate_thermal_specs(state: HeatingWireState):
    errors = []
    if state['specs'].get('max_temp', 0) > 1200:
        errors.append('Temperature exceeds standard safety thresholds')
    return {'validation_errors': errors, 'is_compliant': len(errors) == 0}

def approval_check(state: HeatingWireState):
    return 'approved' if state['is_compliant'] else 'flagged'

graph = StateGraph(HeatingWireState)
graph.add_node('validator', validate_thermal_specs)
graph.add_edge('validator', END)
graph.set_entry_point('validator')
