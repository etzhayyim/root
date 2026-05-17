from typing import TypedDict
from langgraph.graph import StateGraph, END

class SorbitolState(TypedDict):
    purity: float
    gmp_status: bool
    is_compliant: bool

def validate_quality(state: SorbitolState):
    compliant = state['purity'] >= 99.0 and state['gmp_status']
    return {'is_compliant': compliant}

graph = StateGraph(SorbitolState)
graph.add_node('validate', validate_quality)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
app = graph.compile()