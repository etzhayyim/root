from typing import TypedDict
from langgraph.graph import StateGraph, END

class CableState(TypedDict):
    spec: dict
    validated: bool
    error: str

def validate_specs(state: CableState):
    required = ['tensile_strength', 'material']
    if all(k in state['spec'] for k in required):
        return {'validated': True}
    return {'validated': False, 'error': 'Missing required specs'}

def routing(state: CableState):
    return 'validate' if not state.get('validated') else END

graph = StateGraph(CableState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
