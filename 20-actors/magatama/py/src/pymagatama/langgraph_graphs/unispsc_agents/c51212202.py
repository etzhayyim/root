from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class NicotineState(TypedDict):
    purity: float
    destination: str
    compliance_cleared: bool

def validate_purity(state: NicotineState) -> NicotineState:
    if state['purity'] < 0.99:
        raise ValueError('Purity must be at least 99%')
    return state

def check_compliance(state: NicotineState) -> NicotineState:
    state['compliance_cleared'] = True
    return state

graph = StateGraph(NicotineState)
graph.add_node('validate', validate_purity)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
app = graph.compile()
