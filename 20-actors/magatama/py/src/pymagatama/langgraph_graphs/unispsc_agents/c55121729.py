from typing import TypedDict
from langgraph.graph import StateGraph, END

class TokenSpecState(TypedDict):
    material: str
    dimensions: dict
    approved: bool

def validate_specs(state: TokenSpecState):
    if state['dimensions'].get('diameter_mm', 0) > 0 and state['material']:
        return {'approved': True}
    return {'approved': False}

graph = StateGraph(TokenSpecState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()