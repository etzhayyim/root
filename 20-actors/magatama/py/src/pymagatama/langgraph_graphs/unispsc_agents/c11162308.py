from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

class MetalProcurementState(TypedDict):
    material_id: str
    purity_level: float
    compliance_checks: List[str]
    approved: bool

def validate_material_purity(state: MetalProcurementState):
    is_pure = state['purity_level'] >= 99.99
    return {'compliance_checks': ['Purity Validated'] if is_pure else ['Purity Failed']}

def perform_safety_review(state: MetalProcurementState):
    return {'approved': 'Purity Failed' not in state['compliance_checks']}

graph = StateGraph(MetalProcurementState)
graph.add_node('validate', validate_material_purity)
graph.add_node('safety', perform_safety_review)
graph.set_entry_point('validate')
graph.add_edge('validate', 'safety')
graph.add_edge('safety', END)
graph = graph.compile()
