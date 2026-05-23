from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class TriacetinState(TypedDict):
    purity: float
    moisture: float
    compliant: bool

def validate_specs(state: TriacetinState):
    compliant = state['purity'] >= 99.0 and state['moisture'] <= 0.2
    return {'compliant': compliant}

graph = StateGraph(TriacetinState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
