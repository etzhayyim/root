from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class WaterProcurementState(TypedDict):
    purity_level: float
    volume: float
    delivery_date: str
    inspection_results: List[str]

def validate_purity(state: WaterProcurementState):
    if state['purity_level'] < 18.2:
        return {'inspection_results': state['inspection_results'] + ['Purity below threshold']}
    return {'inspection_results': state['inspection_results'] + ['Purity verified']}

def schedule_delivery(state: WaterProcurementState):
    return {'inspection_results': state['inspection_results'] + ['Delivery scheduled']}

graph = StateGraph(WaterProcurementState)
graph.add_node('validate', validate_purity)
graph.add_node('delivery', schedule_delivery)
graph.add_edge('validate', 'delivery')
graph.add_edge('delivery', END)
graph.set_entry_point('validate')
compiled_graph = graph.compile()
