from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    batch_id: str
    compliance_cleared: bool
    is_expired: bool

def validate_compliance(state: ProcurementState):
    state['compliance_cleared'] = True
    return 'check_batch'

def check_batch(state: ProcurementState):
    state['is_expired'] = False
    return END

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_compliance)
graph.add_node('check_batch', check_batch)
graph.set_entry_point('validate')
graph.add_edge('validate', 'check_batch')
graph.add_edge('check_batch', END)
app = graph.compile()
