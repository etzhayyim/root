from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class BerylliumState(TypedDict):
    material_specs: dict
    compliance_checks: List[str]
    approved: bool

def validate_material(state: BerylliumState):
    checks = []
    if 'purity' in state['material_specs'] and state['material_specs']['purity'] >= 99.0:
        checks.append('Purity Verified')
    return {'compliance_checks': checks}

def safety_routing(state: BerylliumState):
    if 'Toxicity-SDS' in state['material_specs']:
        return 'final'
    return END

graph = StateGraph(BerylliumState)
graph.add_node('validate', validate_material)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
graph = graph.compile()