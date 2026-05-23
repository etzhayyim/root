from typing import TypedDict
from langgraph.graph import StateGraph, END

class FoodSupplyState(TypedDict):
    quality_docs: dict
    brix_level: float
    status: str

def validate_quality(state: FoodSupplyState):
    is_safe = state['brix_level'] >= 50.0 and 'cert' in state['quality_docs']
    return {'status': 'approved' if is_safe else 'rejected'}

def process_shipment(state: FoodSupplyState):
    return {'status': 'processed'}

graph = StateGraph(FoodSupplyState)
graph.add_node('validate', validate_quality)
graph.add_node('ship', process_shipment)
graph.set_entry_point('validate')
graph.add_edge('validate', 'ship')
graph.add_edge('ship', END)
app = graph.compile()
