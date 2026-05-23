from typing import TypedDict
from langgraph.graph import StateGraph, END
class ZincState(TypedDict):
    dimensions: dict
    purity: float
    verified: bool

def validate_specs(state: ZincState):
    state['verified'] = state['purity'] >= 99.9 and 'thickness' in state['dimensions']
    return 'verified' if state['verified'] else 'rejected'

graph = StateGraph(ZincState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
app = graph.compile()
