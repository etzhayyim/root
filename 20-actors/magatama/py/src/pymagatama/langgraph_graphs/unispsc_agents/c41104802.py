from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class DistillationOrderState(TypedDict):
    spec_requirements: dict
    validation_checks: List[str]
    is_compliant: bool

def validate_specs(state: DistillationOrderState):
    checks = []
    if 'material' in state['spec_requirements']: checks.append('MATERIAL_VERIFIED')
    if 'purity' in state['spec_requirements']: checks.append('PURITY_VERIFIED')
    return {'validation_checks': checks, 'is_compliant': len(checks) >= 2}

graph = StateGraph(DistillationOrderState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()