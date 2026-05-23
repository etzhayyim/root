from typing import TypedDict
from langgraph.graph import StateGraph, END

class PharmaState(TypedDict):
    purity: float
    reg_compliant: bool
    passed_qa: bool

def validate_purity(state: PharmaState):
    state['passed_qa'] = state['purity'] >= 99.0
    return state

def check_compliance(state: PharmaState):
    state['reg_compliant'] = True
    return state

graph = StateGraph(PharmaState)
graph.add_node('validate', validate_purity)
graph.add_node('compliance', check_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()
