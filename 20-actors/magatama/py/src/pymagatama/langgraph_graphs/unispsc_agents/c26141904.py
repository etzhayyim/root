from typing import TypedDict
from langgraph.graph import StateGraph, END

class GaugeState(TypedDict):
    specs: dict
    compliance_cleared: bool
    safety_audit_required: bool

def validate_safety_protocols(state: GaugeState):
    radiation_source = state['specs'].get('source_type')
    state['compliance_cleared'] = radiation_source is not None
    return state

def check_regulatory_license(state: GaugeState):
    state['safety_audit_required'] = True
    return state

graph = StateGraph(GaugeState)
graph.add_node('validate', validate_safety_protocols)
graph.add_node('compliance', check_regulatory_license)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
