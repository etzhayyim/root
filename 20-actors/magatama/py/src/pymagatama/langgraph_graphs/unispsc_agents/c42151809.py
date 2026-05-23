from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class DentalSupplyState(TypedDict):
    item_name: str
    specs: dict
    approved: bool
    compliance_checks: List[str]

def validate_biocompatibility(state: DentalSupplyState):
    checks = state.get('compliance_checks', [])
    if 'iso_10993' in state['specs'].get('certifications', []):
        checks.append('Biocompatibility Verified')
    return {'compliance_checks': checks}

def inspect_material(state: DentalSupplyState):
    is_sterile = state['specs'].get('sterility') == 'high_grade'
    return {'approved': is_sterile}

graph = StateGraph(DentalSupplyState)
graph.add_node('validate', validate_biocompatibility)
graph.add_node('inspect', inspect_material)
graph.set_entry_point('validate')
graph.add_edge('validate', 'inspect')
graph.add_edge('inspect', END)
graph = graph.compile()
