from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class ChemicalProcurementState(TypedDict):
    material_id: str
    purity_level: float
    safety_compliant: bool
    validation_steps: List[str]

def validate_material(state: ChemicalProcurementState):
    # Simulate chemical validation logic
    state['validation_steps'].append('Compliance check: SDS and Purity Verification')
    state['safety_compliant'] = state['purity_level'] >= 0.99
    return state

def route_procurement(state: ChemicalProcurementState):
    return 'VALIDATED' if state['safety_compliant'] else 'REJECTED'

graph = StateGraph(ChemicalProcurementState)
graph.add_node('validate', validate_material)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_procurement, {'VALIDATED': END, 'REJECTED': END})

graph = graph.compile()