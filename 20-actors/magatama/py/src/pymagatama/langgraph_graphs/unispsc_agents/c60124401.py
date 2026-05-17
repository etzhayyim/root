from typing import TypedDict
from langgraph.graph import StateGraph, END

class FoilState(TypedDict):
    purity: float
    thickness: float
    compliance_docs: bool
    approved: bool

def validate_specs(state: FoilState):
    if state['purity'] >= 99.9 and state['thickness'] > 0:
        return {'approved': True}
    return {'approved': False}

graph = StateGraph(FoilState)
graph.add_node('validation', validate_specs)
graph.set_entry_point('validation')
graph.add_edge('validation', END)
graph = graph.compile()