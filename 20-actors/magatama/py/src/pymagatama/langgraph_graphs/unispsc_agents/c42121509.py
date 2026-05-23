from typing import TypedDict
from langgraph.graph import StateGraph, END

class VThermState(TypedDict):
    spec_data: dict
    validated: bool
    error: str

def validate_specs(state: VThermState):
    required = ['accuracy', 'range', 'certification']
    if all(k in state['spec_data'] for k in required):
        return {'validated': True}
    return {'validated': False, 'error': 'Missing required technical specs'}

def route_by_validation(state: VThermState):
    return 'validate' if not state['validated'] else END

graph = StateGraph(VThermState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
