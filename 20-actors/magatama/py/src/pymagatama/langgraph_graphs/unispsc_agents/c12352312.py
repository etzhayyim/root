from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class ChemicalProcurementState(TypedDict):
    material_id: str
    purity_level: float
    compliance_checks: Annotated[Sequence[str], operator.add]
    is_approved: bool

def validate_purity(state: ChemicalProcurementState) -> dict:
    if state['purity_level'] >= 99.9:
        return {'compliance_checks': ['purity_verified']}
    return {'compliance_checks': ['purity_failed']}

def safety_review(state: ChemicalProcurementState) -> dict:
    if 'purity_verified' in state['compliance_checks']:
        return {'is_approved': True}
    return {'is_approved': False}

graph = StateGraph(ChemicalProcurementState)
graph.add_node('validate_purity', validate_purity)
graph.add_node('safety_review', safety_review)
graph.set_entry_point('validate_purity')
graph.add_edge('validate_purity', 'safety_review')
graph.add_edge('safety_review', END)

graph = graph.compile()