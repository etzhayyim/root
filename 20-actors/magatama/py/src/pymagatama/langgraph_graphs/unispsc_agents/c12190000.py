from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class ChemicalProcurementState(TypedDict):
    material_id: str
    purity_level: float
    compliance_checks: Annotated[Sequence[str], operator.add]
    is_approved: bool

def validate_purity(state: ChemicalProcurementState):
    if state['purity_level'] < 99.9:
        return {'compliance_checks': ['LOW_PURITY_REJECTED'], 'is_approved': False}
    return {'compliance_checks': ['PURITY_PASSED'], 'is_approved': True}

def security_review(state: ChemicalProcurementState):
    if not state['is_approved']:
        return {'compliance_checks': ['SKIPPED_SECURITY']}
    return {'compliance_checks': ['DUAL_USE_REVIEW_COMPLETE']}

graph = StateGraph(ChemicalProcurementState)
graph.add_node('validate', validate_purity)
graph.add_node('security', security_review)
graph.add_edge('validate', 'security')
graph.add_edge('security', END)
graph.set_entry_point('validate')
graph = graph.compile()