from typing import TypedDict
from langgraph.graph import StateGraph, END

class ChemicalProcurementState(TypedDict):
    purity_level: float
    compliance_cert: str
    is_approved: bool

def validate_chemical_specs(state: ChemicalProcurementState) -> dict:
    # Logic to verify chemical purity and regulatory compliance
    if state['purity_level'] >= 99.0 and state['compliance_cert']:
        return {'is_approved': True}
    return {'is_approved': False}

def route_by_validation(state: ChemicalProcurementState) -> str:
    return 'approved' if state['is_approved'] else 'rejected'

graph = StateGraph(ChemicalProcurementState)
graph.add_node('validate', validate_chemical_specs)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_validation, {'approved': END, 'rejected': END})
compiled_graph = graph.compile()
