from typing import TypedDict
from langgraph.graph import StateGraph, END

class PeachProcessingState(TypedDict):
    batch_id: str
    quality_score: float
    is_safe: bool

def validate_food_safety(state: PeachProcessingState):
    state['is_safe'] = state['quality_score'] > 85.0
    return state

def route_by_safety(state: PeachProcessingState):
    return 'process_batch' if state['is_safe'] else 'reject_batch'

graph = StateGraph(PeachProcessingState)
graph.add_node('validate', validate_food_safety)
graph.add_node('process_batch', lambda s: s)
graph.add_node('reject_batch', lambda s: s)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_safety, {'process_batch': 'process_batch', 'reject_batch': 'reject_batch'})
graph.add_edge('process_batch', END)
graph.add_edge('reject_batch', END)
graph = graph.compile()
