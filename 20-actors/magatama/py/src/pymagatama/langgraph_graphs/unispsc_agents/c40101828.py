from typing import TypedDict
from langgraph.graph import StateGraph, END

class HeaterSpecState(TypedDict):
    specs: dict
    validation_errors: list
    is_compliant: bool

def validate_heater_specs(state: HeaterSpecState):
    errors = []
    if state['specs'].get('wattage', 0) <= 0:
        errors.append('Invalid wattage')
    if not state['specs'].get('sheath_material'):
        errors.append('Missing material spec')
    return {'validation_errors': errors, 'is_compliant': len(errors) == 0}

def route_by_compliance(state: HeaterSpecState):
    return 'compliant_path' if state['is_compliant'] else 'reject_path'

graph = StateGraph(HeaterSpecState)
graph.add_node('validate', validate_heater_specs)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_compliance, {'compliant_path': END, 'reject_path': END})
graph.compile()
