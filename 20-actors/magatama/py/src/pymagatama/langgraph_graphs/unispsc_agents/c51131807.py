from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    batch_id: str
    quality_status: bool
    compliance_checked: bool

def validate_batch(state: ProcurementState):
    if state['batch_id']:
        return {'quality_status': True}
    return {'quality_status': False}

def check_compliance(state: ProcurementState):
    return {'compliance_checked': True}

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_batch)
graph.add_node('compliance', check_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()