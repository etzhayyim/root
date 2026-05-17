from typing import TypedDict
from langgraph.graph import StateGraph, END

class FoodProcurementState(TypedDict):
    product_name: str
    moisture_content: float
    inspection_passed: bool

def validate_dry_goods(state: FoodProcurementState):
    # Thresholds for preserved fruit quality
    if state['moisture_content'] < 0.25:
        return {'inspection_passed': True}
    return {'inspection_passed': False}

def route_by_inspection(state: FoodProcurementState):
    return 'approve' if state['inspection_passed'] else 'reject'

graph_builder = StateGraph(FoodProcurementState)
graph_builder.add_node('validate', validate_dry_goods)
graph_builder.add_edge('validate', END)
graph_builder.set_entry_point('validate')
graph = graph_builder.compile()