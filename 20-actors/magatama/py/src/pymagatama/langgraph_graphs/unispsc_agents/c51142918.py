from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ArticaineState(TypedDict):
    batch_number: str
    purity_level: float
    has_sterility_cert: bool
    status: str

def validate_purity(state: ArticaineState):
    state['status'] = 'VALIDATED' if state['purity_level'] >= 99.0 else 'REJECTED'
    return state

def check_compliance(state: ArticaineState):
    if state['status'] == 'VALIDATED' and state['has_sterility_cert']:
        state['status'] = 'APPROVED'
    return state

graph = StateGraph(ArticaineState)
graph.add_node('validate', validate_purity)
graph.add_node('compliance', check_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()
