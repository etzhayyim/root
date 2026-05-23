from typing import TypedDict
from langgraph.graph import StateGraph, END

class SurgicalGownState(TypedDict):
    spec_data: dict
    approved: bool

def validate_barrier_performance(state: SurgicalGownState):
    level = state['spec_data'].get('AAMI_level', 0)
    return {'approved': level >= 3}

def check_compliance(state: SurgicalGownState):
    has_cert = 'ISO_13485' in state['spec_data'].get('certifications', [])
    return {'approved': state['approved'] and has_cert}

graph = StateGraph(SurgicalGownState)
graph.add_node('validate_barrier', validate_barrier_performance)
graph.add_node('compliance_check', check_compliance)
graph.set_entry_point('validate_barrier')
graph.add_edge('validate_barrier', 'compliance_check')
graph.add_edge('compliance_check', END)
graph = graph.compile()
