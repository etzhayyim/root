from typing import TypedDict
from langgraph.graph import StateGraph, END

class SplintProcurementState(TypedDict):
    item_id: str
    compliance_verified: bool
    spec_approved: bool

def validate_compliance(state: SplintProcurementState):
    state['compliance_verified'] = True
    return 'compliance_verified'

def review_specs(state: SplintProcurementState):
    state['spec_approved'] = True
    return 'spec_approved'

graph = StateGraph(SplintProcurementState)
graph.add_node('validate_compliance', validate_compliance)
graph.add_node('review_specs', review_specs)
graph.set_entry_point('validate_compliance')
graph.add_edge('validate_compliance', 'review_specs')
graph.add_edge('review_specs', END)

app = graph.compile()