from typing import TypedDict
from langgraph.graph import StateGraph, END

class FastenerState(TypedDict):
    spec_data: dict
    validated: bool
    error_log: list

def validate_specs(state: FastenerState):
    required = ['Material Grade', 'Dimensional Standard']
    errors = [f for f in required if f not in state['spec_data']]
    return {'validated': len(errors) == 0, 'error_log': errors}

def route_by_validation(state: FastenerState):
    return 'validate' if not state.get('validated') else END

graph = StateGraph(FastenerState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph.compile()
