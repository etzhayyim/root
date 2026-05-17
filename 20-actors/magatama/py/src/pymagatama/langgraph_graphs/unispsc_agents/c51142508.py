from typing import TypedDict
from langgraph.graph import StateGraph, END

class PharmState(TypedDict):
    purity: float
    compliant: bool
    error: str

def validate_purity(state: PharmState):
    if state['purity'] < 99.0:
        return {'compliant': False, 'error': 'Purity below threshold'}
    return {'compliant': True, 'error': None}

graph = StateGraph(PharmState)
graph.add_node('validate', validate_purity)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()