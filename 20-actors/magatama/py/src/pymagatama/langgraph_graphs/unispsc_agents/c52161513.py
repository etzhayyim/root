from typing import TypedDict
from langgraph.graph import StateGraph, END

class VCRTVState(TypedDict):
    specs: dict
    is_validated: bool
    error_log: list

def validate_specs(state: VCRTVState):
    required = ['tuner_type', 'voltage']
    missing = [f for f in required if f not in state['specs']]
    return {'is_validated': len(missing) == 0, 'error_log': missing}

def route_by_validation(state: VCRTVState):
    return 'valid' if state['is_validated'] else 'invalid'

graph = StateGraph(VCRTVState)
graph.add_node('validate', validate_specs)
graph.add_conditional_edges('validate', route_by_validation, {'valid': END, 'invalid': END})
graph.set_entry_point('validate')