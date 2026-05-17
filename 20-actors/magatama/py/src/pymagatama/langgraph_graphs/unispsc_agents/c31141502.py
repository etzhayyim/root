from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class RubberState(TypedDict):
    requirements: dict
    validation_errors: List[str]
    is_approved: bool

def validate_rubber_specs(state: RubberState):
    errors = []
    if state['requirements'].get('durometer_hardness', 0) < 30:
        errors.append('Hardness value too low for structural integrity.')
    return {'validation_errors': errors, 'is_approved': len(errors) == 0}

def check_thermal_tolerance(state: RubberState):
    if state['requirements'].get('temp_celsius', 0) > 150:
        return {'is_approved': True}
    return {'is_approved': False}

graph = StateGraph(RubberState)
graph.add_node('validate', validate_rubber_specs)
graph.add_node('thermal_check', check_thermal_tolerance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'thermal_check')
graph.add_edge('thermal_check', END)
graph = graph.compile()