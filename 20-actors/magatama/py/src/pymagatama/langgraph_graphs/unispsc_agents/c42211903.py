from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    product_id: str
    accessibility_score: float
    safety_compliance: bool

def validate_accessibility(state: ProcurementState) -> dict:
    if state['accessibility_score'] < 0.8:
        return {'safety_compliance': False}
    return {'safety_compliance': True}

def finalize_procurement(state: ProcurementState) -> dict:
    return {'product_id': f'VERIFIED_{state["product_id"]}'}

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_accessibility)
graph.add_node('finish', finalize_procurement)
graph.set_entry_point('validate')
graph.add_edge('validate', 'finish')
graph.add_edge('finish', END)
graph = graph.compile()
