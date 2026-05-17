from typing import TypedDict
from langgraph.graph import StateGraph, END

class CastingState(TypedDict):
    spec_data: dict
    validated: bool
    error_log: list

def validate_specs(state: CastingState):
    required = ['Material Grade', 'Dimensional Tolerance']
    missing = [f for f in required if f not in state['spec_data']]
    return {'validated': len(missing) == 0, 'error_log': missing}

def route_verification(state: CastingState):
    return 'valid' if state['validated'] else 'invalid'

graph = StateGraph(CastingState)
graph.add_node('validate', validate_specs)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
graph = graph.compile()