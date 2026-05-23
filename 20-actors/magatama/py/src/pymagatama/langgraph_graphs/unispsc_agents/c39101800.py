from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class LightingProcurementState(TypedDict):
    component_list: List[str]
    compliance_checks: List[str]
    is_approved: bool

def validate_specs(state: LightingProcurementState):
    checks = [c for c in state['component_list'] if 'certified' in c]
    return {'compliance_checks': checks, 'is_approved': len(checks) > 0}

graph = StateGraph(LightingProcurementState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
