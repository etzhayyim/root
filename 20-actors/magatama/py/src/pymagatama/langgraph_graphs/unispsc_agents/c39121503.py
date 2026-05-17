from typing import TypedDict
from langgraph.graph import StateGraph, END

class SwitchState(TypedDict):
    specs: dict
    validated: bool
    error: str

def validate_specs(state: SwitchState):
    required = ['voltage', 'amp', 'ip_rating']
    if all(k in state['specs'] for k in required):
        return {'validated': True}
    return {'validated': False, 'error': 'Missing technical specifications'}

def route_by_validation(state: SwitchState):
    return 'validate' if not state['validated'] else END

graph = StateGraph(SwitchState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)

app = graph.compile()