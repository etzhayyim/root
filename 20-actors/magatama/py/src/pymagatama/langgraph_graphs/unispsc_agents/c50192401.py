from typing import TypedDict
from langgraph.graph import StateGraph, END

class FoodProcurementState(TypedDict):
    product_name: str
    quality_score: float
    haccp_compliant: bool

def validate_food_specs(state: FoodProcurementState):
    if state['haccp_compliant']:
        return {'quality_score': 1.0}
    return {'quality_score': 0.0}

graph = StateGraph(FoodProcurementState)
graph.add_node('validate', validate_food_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()