from typing import TypedDict
from langgraph.graph import StateGraph, END

class RadiatorState(TypedDict):
    spec_data: dict
    validated: bool
    error_log: list

def validate_specs(state: RadiatorState):
    specs = state['spec_data']
    errors = []
    if specs.get('pressure_rating', 0) < 150: errors.append('Pressure rating insufficient')
    return {'validated': len(errors) == 0, 'error_log': errors}

def route_by_validation(state: RadiatorState):
    return 'process_order' if state['validated'] else 'reject_order'

graph = StateGraph(RadiatorState)
graph.add_node('validate', validate_specs)
graph.add_node('process_order', lambda x: x)
graph.add_node('reject_order', lambda x: x)
graph.add_edge('validate', 'process_order')
graph.set_entry_point('validate')
