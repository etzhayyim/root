from typing import TypedDict
from langgraph.graph import StateGraph, END

class GolfState(TypedDict):
    specs: dict
    is_validated: bool

def validate_specs(state: GolfState):
    required = ['material', 'dimensions', 'target_user_level']
    valid = all(k in state['specs'] for k in required)
    return {'is_validated': valid}

def route_by_validation(state: GolfState):
    return 'valid' if state['is_validated'] else 'invalid'

graph = StateGraph(GolfState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_validation, {'valid': END, 'invalid': END})
