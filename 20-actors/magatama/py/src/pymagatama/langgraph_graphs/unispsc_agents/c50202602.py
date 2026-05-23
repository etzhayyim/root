from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class JuiceState(TypedDict):
    batch_id: str
    quality_passed: bool
    brix_level: float
    specs: dict

def validate_brix(state: JuiceState):
    passed = state['brix_level'] >= 11.5
    return {'quality_passed': passed}

def route_quality(state: JuiceState):
    return 'process_shipment' if state['quality_passed'] else 'flag_rejection'

graph = StateGraph(JuiceState)
graph.add_node('validate', validate_brix)
graph.add_node('process_shipment', lambda s: {'status': 'approved'})
graph.add_node('flag_rejection', lambda s: {'status': 'rejected'})
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_quality)
graph.add_edge('process_shipment', END)
graph.add_edge('flag_rejection', END)
graph = graph.compile()
