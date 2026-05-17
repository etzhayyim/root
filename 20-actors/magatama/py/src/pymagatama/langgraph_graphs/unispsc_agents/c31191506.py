from typing import TypedDict
from langgraph.graph import StateGraph, END

class AbrasiveSpecs(TypedDict):
    grit: str
    diameter: float
    max_rpm: int
    compliant: bool

def validate_specs(state: AbrasiveSpecs):
    if state['max_rpm'] < 0:
        return {'compliant': False}
    return {'compliant': True}

graph = StateGraph(AbrasiveSpecs)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()