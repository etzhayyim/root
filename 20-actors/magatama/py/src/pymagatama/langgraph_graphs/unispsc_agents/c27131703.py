from typing import TypedDict
from langgraph.graph import StateGraph, END

class PistonState(TypedDict):
    specs: dict
    validated: bool

def validate_specs(state: PistonState) -> PistonState:
    s = state['specs']
    state['validated'] = all(k in s for k in ['pressure_rating', 'material'])
    print('Validating pneumatic piston specifications...')
    return state

def check_compliance(state: PistonState) -> str:
    return 'valid' if state['validated'] else 'invalid'

graph = StateGraph(PistonState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()