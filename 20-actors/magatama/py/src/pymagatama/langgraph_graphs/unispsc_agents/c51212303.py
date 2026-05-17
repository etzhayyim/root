from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    purity_level: float
    compliance_checked: bool
    approved: bool

def validate_purity(state: ProcurementState):
    state['compliance_checked'] = state['purity_level'] >= 99.0
    return state

def check_regulatory(state: ProcurementState):
    state['approved'] = state['compliance_checked']
    return state

graph = StateGraph(ProcurementState)
graph.add_node('validate_purity', validate_purity)
graph.add_node('check_regulatory', check_regulatory)
graph.add_edge('validate_purity', 'check_regulatory')
graph.add_edge('check_regulatory', END)
graph.set_entry_point('validate_purity')
graph = graph.compile()