from typing import TypedDict
from langgraph.graph import StateGraph, END

class FuseState(TypedDict):
    spec_data: dict
    validated: bool
    error_log: list

def validate_fuse_specs(state: FuseState):
    required = ['voltage', 'amperage', 'standard']
    errors = [field for field in required if field not in state['spec_data']]
    return {'validated': len(errors) == 0, 'error_log': errors}

def route_by_validation(state: FuseState):
    return 'valid' if state['validated'] else 'invalid'

graph = StateGraph(FuseState)
graph.add_node('validate', validate_fuse_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph.compile()
