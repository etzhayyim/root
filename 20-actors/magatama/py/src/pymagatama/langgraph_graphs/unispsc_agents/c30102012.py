from typing import TypedDict
from langgraph.graph import StateGraph, END

class ZincProcurementState(TypedDict):
    purity: float
    thickness: float
    compliance_check: bool
    approved: bool

def validate_specs(state: ZincProcurementState):
    if state['purity'] >= 99.9:
        return {'compliance_check': True}
    return {'compliance_check': False}

def approval_step(state: ZincProcurementState):
    return {'approved': state['compliance_check']}

graph = StateGraph(ZincProcurementState)
graph.add_node('validate', validate_specs)
graph.add_node('approve', approval_step)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph = graph.compile()