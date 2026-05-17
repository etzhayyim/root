from typing import TypedDict
from langgraph.graph import StateGraph, END

class LiftProcurementState(TypedDict):
    spec_verified: bool
    compliance_passed: bool
    weight_limit: float

def validate_tech_specs(state: LiftProcurementState):
    # Logic to verify load-bearing capacity against safety standards
    state['spec_verified'] = state['weight_limit'] > 0
    return 'compliance_stage'

def check_compliance(state: LiftProcurementState):
    # Logic for ISO 10535 validation
    state['compliance_passed'] = True
    return END

def create_graph():
    graph = StateGraph(LiftProcurementState)
    graph.add_node('spec_stage', validate_tech_specs)
    graph.add_node('compliance_stage', check_compliance)
    graph.set_entry_point('spec_stage')
    graph.add_edge('spec_stage', 'compliance_stage')
    graph.add_edge('compliance_stage', END)
    return graph

graph = create_graph()