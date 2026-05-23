from typing import TypedDict
from langgraph.graph import StateGraph, END

class MotorState(TypedDict):
    specs: dict
    validated: bool
    error_log: list

def validate_specs(state: MotorState):
    required = ['voltage', 'torque', 'rpm']
    errors = [f'Missing {f}' for f in required if f not in state['specs']]
    return {'validated': len(errors) == 0, 'error_log': errors}

def route_by_validation(state: MotorState):
    return 'valid' if state['validated'] else 'invalid'

graph = StateGraph(MotorState)
graph.add_node('validate', validate_specs)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
graph = graph.compile()
