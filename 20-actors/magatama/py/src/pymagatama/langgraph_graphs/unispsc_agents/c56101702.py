from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class FilingSpecState(TypedDict):
    dimensions: dict
    security_level: str
    is_compliant: bool

def validate_specs(state: FilingSpecState):
    # Business logic for filing system compliance check
    required_keys = ['width', 'height', 'depth']
    state['is_compliant'] = all(k in state['dimensions'] for k in required_keys)
    return state

graph = StateGraph(FilingSpecState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
