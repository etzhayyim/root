from typing import TypedDict
from langgraph.graph import StateGraph, END

class AlarmState(TypedDict):
    specs: dict
    validated: bool
    error_log: list

def validate_specs(state: AlarmState):
    required = ['db_level', 'voltage']
    errors = [k for k in required if k not in state['specs']]
    return {'validated': len(errors) == 0, 'error_log': errors}

def route_by_validation(state: AlarmState):
    return 'valid' if state['validated'] else 'invalid'

graph = StateGraph(AlarmState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_validation, {'valid': END, 'invalid': END})
graph.compile()