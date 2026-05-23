from typing import TypedDict
from langgraph.graph import StateGraph, END

class NatamycinState(TypedDict):
    purity: float
    safety_check: bool
    approved: bool

def validate_purity(state: NatamycinState):
    state['approved'] = state['purity'] >= 95.0
    return 'purity_check' in state

def safety_compliance(state: NatamycinState):
    state['safety_check'] = True
    return state

graph = StateGraph(NatamycinState)
graph.add_node('validate', validate_purity)
graph.add_node('safety', safety_compliance)
graph.add_edge('validate', 'safety')
graph.add_edge('safety', END)
graph.set_entry_point('validate')
graph = graph.compile()
