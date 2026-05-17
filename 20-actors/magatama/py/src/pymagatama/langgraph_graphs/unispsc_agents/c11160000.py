from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class RawMaterialState(TypedDict):
    material_type: str
    purity_required: float
    compliance_checks: List[str]
    is_approved: bool

def validate_purity(state: RawMaterialState) -> RawMaterialState:
    if state.get('purity_required', 0) >= 95.0:
        state['is_approved'] = True
    else:
        state['is_approved'] = False
    return state

def perform_compliance_check(state: RawMaterialState) -> RawMaterialState:
    state['compliance_checks'].append('sanctions_scrub_complete')
    return state

graph = StateGraph(RawMaterialState)
graph.add_node('validate', validate_purity)
graph.add_node('compliance', perform_compliance_check)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()