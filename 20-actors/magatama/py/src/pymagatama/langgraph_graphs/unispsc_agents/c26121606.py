from typing import TypedDict
from langgraph.graph import StateGraph, END

class CableState(TypedDict):
    specs: dict
    validated: bool
    error: str

def validate_specs(state: CableState):
    s = state['specs']
    valid = all([s.get('impedance') in [50, 75], s.get('attenuation', 0) < 10])
    return {'validated': valid, 'error': None if valid else 'Invalid electrical specs'}

def update_status(state: CableState):
    return {'validated': state['validated']}

graph = StateGraph(CableState)
graph.add_node('validator', validate_specs)
graph.add_node('logger', update_status)
graph.add_edge('validator', 'logger')
graph.add_edge('logger', END)
graph.set_entry_point('validator')
graph = graph.compile()
