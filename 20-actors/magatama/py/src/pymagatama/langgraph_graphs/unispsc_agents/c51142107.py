from typing import TypedDict
from langgraph.graph import StateGraph, END

class DrugState(TypedDict):
    batch_number: str
    purity_level: float
    compliance_checked: bool

def validate_purity(state: DrugState):
    state['compliance_checked'] = state['purity_level'] >= 99.0
    return state

def route_verification(state: DrugState):
    return 'process' if state['compliance_checked'] else 'reject'

graph = StateGraph(DrugState)
graph.add_node('verify', validate_purity)
graph.set_entry_point('verify')
graph.add_edge('verify', END)
graph.compile()
