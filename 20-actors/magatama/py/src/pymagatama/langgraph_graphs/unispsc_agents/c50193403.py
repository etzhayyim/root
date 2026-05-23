from typing import TypedDict
from langgraph.graph import StateGraph, END

class BlueberryState(TypedDict):
    quality_score: float
    moisture_content: float
    is_compliant: bool

def validate_batch(state: BlueberryState):
    if state['moisture_content'] < 0.15 and state['quality_score'] > 80:
        return {'is_compliant': True}
    return {'is_compliant': False}

def process_shipment(state: BlueberryState):
    print('Proceeding with shipment sanitization')
    return {'is_compliant': True}

graph = StateGraph(BlueberryState)
graph.add_node('validate', validate_batch)
graph.add_node('shipment', process_shipment)
graph.add_edge('validate', 'shipment')
graph.add_edge('shipment', END)
graph.set_entry_point('validate')
graph = graph.compile()
