from typing import TypedDict
from langgraph.graph import StateGraph, END

class LimeState(TypedDict):
    brix: float
    acidity: float
    qc_passed: bool

def validate_quality(state: LimeState):
    # Validate lime specifications
    is_valid = state['brix'] > 40.0 and state['acidity'] > 5.0
    return {'qc_passed': is_valid}

def process_shipment(state: LimeState):
    return {'qc_passed': True}

graph = StateGraph(LimeState)
graph.add_node('validate', validate_quality)
graph.add_node('ship', process_shipment)
graph.set_entry_point('validate')
graph.add_edge('validate', 'ship')
graph.add_edge('ship', END)
graph = graph.compile()
