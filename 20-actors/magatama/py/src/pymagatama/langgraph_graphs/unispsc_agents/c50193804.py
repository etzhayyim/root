from typing import TypedDict
from langgraph.graph import StateGraph, END

class GrapeState(TypedDict):
    batch_id: str
    inspection_passed: bool
    brix: float

def validate_quality(state: GrapeState):
    if state['brix'] >= 15.0:
        return {'inspection_passed': True}
    return {'inspection_passed': False}

def process_shipment(state: GrapeState):
    return {'status': 'READY_FOR_DISTRIBUTION'}

graph = StateGraph(GrapeState)
graph.add_node('validate', validate_quality)
graph.add_node('ship', process_shipment)
graph.add_edge('validate', 'ship')
graph.add_edge('ship', END)
graph.set_entry_point('validate')
graph = graph.compile()