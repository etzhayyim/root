from typing import TypedDict
from langgraph.graph import StateGraph, END

class SprayingMachineState(TypedDict):
    specs: dict
    validation_errors: list
    is_approved: bool

def validate_specs(state: SprayingMachineState):
    errors = []
    if state['specs'].get('tank_capacity_liters', 0) <= 0:
        errors.append('Invalid tank capacity')
    return {'validation_errors': errors, 'is_approved': len(errors) == 0}

def check_safety(state: SprayingMachineState):
    if 'safety_certification' not in state['specs']:
        state['validation_errors'].append('Missing safety certification')
        state['is_approved'] = False
    return state

graph = StateGraph(SprayingMachineState)
graph.add_node('validate', validate_specs)
graph.add_node('safety', check_safety)
graph.set_entry_point('validate')
graph.add_edge('validate', 'safety')
graph.add_edge('safety', END)
graph = graph.compile()
