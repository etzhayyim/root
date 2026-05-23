from typing import TypedDict
from langgraph.graph import StateGraph, END

class SealState(TypedDict):
    specs: dict
    validated: bool
    error: str

def validate_seal_specs(state: SealState):
    required = ['shaft_diameter', 'material', 'pressure_rating']
    if all(k in state['specs'] for k in required):
        return {'validated': True}
    return {'validated': False, 'error': 'Missing required fields'}

def route_by_validation(state: SealState):
    return 'validate' if not state.get('validated') else END

graph = StateGraph(SealState)
graph.add_node('validate', validate_seal_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
