from typing import TypedDict
from langgraph.graph import StateGraph, END

class DrugProcurementState(TypedDict):
    product_name: str
    compliance_check: bool
    purity_level: float
    status: str

def validate_compliance(state: DrugProcurementState):
    return {'compliance_check': True, 'status': 'Validated'}

def check_purity(state: DrugProcurementState):
    is_pure = state['purity_level'] >= 99.0
    return {'status': 'Quality Approved' if is_pure else 'Rejected'}

graph = StateGraph(DrugProcurementState)
graph.add_node('compliance', validate_compliance)
graph.add_node('quality', check_purity)
graph.add_edge('compliance', 'quality')
graph.add_edge('quality', END)
graph.set_entry_point('compliance')
graph = graph.compile()