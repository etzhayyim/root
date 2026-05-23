from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class ChemicalProcurementState(TypedDict):
    material_id: str
    purity_level: float
    compliance_checked: bool
    validation_logs: List[str]

def validate_material(state: ChemicalProcurementState):
    # Simulate stringent chemical validation logic
    is_pure = state['purity_level'] >= 0.99
    return {'compliance_checked': is_pure, 'validation_logs': ['Validation: Purity check complete.']}

def route_procurement(state: ChemicalProcurementState):
    return 'success' if state['compliance_checked'] else 'reject'

graph = StateGraph(ChemicalProcurementState)
graph.add_node('validate', validate_material)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
