from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class AdhesiveProcurementState(TypedDict):
    material_code: str
    quality_checks: List[str]
    safety_clearance: bool
    is_approved: bool

def validate_viscosity(state: AdhesiveProcurementState):
    # Simulate complex viscosity validation logic
    state['quality_checks'].append('viscosity_verified')
    return state

def check_safety_msds(state: AdhesiveProcurementState):
    # Validate compliance
    state['safety_clearance'] = True
    return state

def final_approval(state: AdhesiveProcurementState):
    state['is_approved'] = True
    return state

graph = StateGraph(AdhesiveProcurementState)
graph.add_node('validate', validate_viscosity)
graph.add_node('safety', check_safety_msds)
graph.add_node('approve', final_approval)
graph.add_edge('validate', 'safety')
graph.add_edge('safety', 'approve')
graph.add_edge('approve', END)
graph.set_entry_point('validate')
graph = graph.compile()
