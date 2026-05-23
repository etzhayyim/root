from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class MepivacaineState(TypedDict):
    purity_level: float
    doc_verified: bool
    compliant: bool

def validate_purity(state: MepivacaineState):
    state['compliant'] = state['purity_level'] >= 99.0
    return state

def check_compliance(state: MepivacaineState):
    return 'compliant' if state['compliant'] else 'non_compliant'

graph = StateGraph(MepivacaineState)
graph.add_node('validate', validate_purity)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
app = graph.compile()
