from typing import TypedDict
from langgraph.graph import StateGraph, END

class TractorState(TypedDict):
    spec_data: dict
    validated: bool
    error: str

def validate_specs(state: TractorState):
    required = ['Engine Power', 'Emission Standard']
    if all(k in state['spec_data'] for k in required):
        return {'validated': True}
    return {'validated': False, 'error': 'Missing core specifications'}

def route_verification(state: TractorState):
    return 'validate' if not state.get('validated') else END

graph = StateGraph(TractorState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph.compile()
