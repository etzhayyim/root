from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    drug_name: str
    purity: float
    temp_log_verified: bool
    compliance_cleared: bool

def validate_purity(state: ProcurementState):
    return {'compliance_cleared': state['purity'] >= 99.5}

def check_logistics(state: ProcurementState):
    return {'temp_log_verified': True}

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_purity)
graph.add_node('logistics', check_logistics)
graph.add_edge('validate', 'logistics')
graph.add_edge('logistics', END)
graph.set_entry_point('validate')
app = graph.compile()