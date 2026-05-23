from typing import TypedDict
from langgraph.graph import StateGraph, END

class AntState(TypedDict):
    specs: dict
    validated: bool
    error: str

def validate_specs(state: AntState) -> AntState:
    required = ['frequency_range_ghz', 'ip_rating']
    if all(k in state['specs'] for k in required):
        state['validated'] = True
    else:
        state['validated'] = False
        state['error'] = 'Missing critical antenna specifications'
    return state

def route_by_validation(state: AntState) -> str:
    return 'validate' if not state.get('validated') else END

graph = StateGraph(AntState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)

graph = graph.compile()
