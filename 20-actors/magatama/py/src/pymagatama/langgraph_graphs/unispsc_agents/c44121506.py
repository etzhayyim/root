from typing import TypedDict
from langgraph.graph import StateGraph, END

class EnvelopeState(TypedDict):
    quantity: int
    spec_compliance: bool
    approved: bool

def validate_specs(state: EnvelopeState):
    state['spec_compliance'] = state['quantity'] > 0
    return state

def approval_check(state: EnvelopeState):
    state['approved'] = state['spec_compliance']
    return state

graph = StateGraph(EnvelopeState)
graph.add_node('validate', validate_specs)
graph.add_node('approve', approval_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
app = graph.compile()
