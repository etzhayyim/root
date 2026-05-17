from typing import TypedDict
from langgraph.graph import StateGraph, END

class FoodState(TypedDict):
    product_name: str
    quality_score: float
    safety_cleared: bool

def validate_cranberry(state: FoodState):
    # Business logic for preserved food verification
    state['safety_cleared'] = state['quality_score'] > 0.8
    return state

def update_status(state: FoodState):
    return {'status': 'Approved' if state['safety_cleared'] else 'Rejected'}

graph = StateGraph(FoodState)
graph.add_node('validate', validate_cranberry)
graph.add_node('finalize', update_status)
graph.set_entry_point('validate')
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph = graph.compile()