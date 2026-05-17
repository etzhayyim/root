from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    product_name: str
    quality_metrics: dict
    approved: bool

def validate_food_safety(state: ProcurementState):
    temp = state['quality_metrics'].get('storage_temp', 25)
    is_safe = temp <= 5
    return {'approved': is_safe}

def finalize_order(state: ProcurementState):
    return {'approved': True}

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_food_safety)
graph.add_node('finalize', finalize_order)
graph.set_entry_point('validate')
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph = graph.compile()