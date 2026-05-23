from typing import TypedDict
from langgraph.graph import StateGraph, END

class WasherState(TypedDict):
    specs: dict
    validated: bool
    error: str

def validate_spec(state: WasherState) -> WasherState:
    required = ['Material Grade', 'Outer Diameter', 'Thread Size']
    if all(k in state['specs'] for k in required):
        state['validated'] = True
    else:
        state['validated'] = False
        state['error'] = 'Missing critical specs'
    return state

def route_step(state: WasherState) -> str:
    return 'validate' if state['validated'] else END

graph = StateGraph(WasherState)
graph.add_node('validate', validate_spec)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
app = graph.compile()
