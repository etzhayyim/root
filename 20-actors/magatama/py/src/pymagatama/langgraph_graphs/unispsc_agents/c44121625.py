from typing import TypedDict, List
from langgraph.graph import StateGraph, END
class ProcurementState(TypedDict):
    item_name: str
    weight_grams: float
    material: str
    is_approved: bool
def validate_specs(state: ProcurementState) -> dict:
    approved = state['weight_grams'] > 0 and state['material'] != ''
    return {'is_approved': approved}
def finalize_order(state: ProcurementState) -> str:
    return 'APPROVED' if state['is_approved'] else 'REJECTED'
graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_specs)
graph.add_node('finalize', finalize_order)
graph.set_entry_point('validate')
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
app = graph.compile()
