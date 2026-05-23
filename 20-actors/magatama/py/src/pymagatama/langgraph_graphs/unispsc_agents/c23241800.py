from typing import TypedDict
from langgraph.graph import StateGraph, END

class DrillingMachineState(TypedDict):
    specs: dict
    validation_errors: list
    is_approved: bool

def validate_specs(state: DrillingMachineState):
    errors = []
    if state['specs'].get('power', 0) < 0.5: errors.append('Insufficient power')
    return {'validation_errors': errors, 'is_approved': len(errors) == 0}

def route_by_validation(state: DrillingMachineState):
    return 'approved' if state['is_approved'] else 'rejected'

graph = StateGraph(DrillingMachineState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)

graph = graph.compile()
