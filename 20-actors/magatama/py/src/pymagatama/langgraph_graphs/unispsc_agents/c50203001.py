from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ConcentrateState(TypedDict):
    brics_level: float
    safety_certs: List[str]
    approved: bool

def validate_quality(state: ConcentrateState):
    if state['brics_level'] < 40.0:
        return {'approved': False}
    return {'approved': True}

def process_shipment(state: ConcentrateState):
    print('Proceeding with cold chain logistics setup.')
    return {'approved': True}

graph = StateGraph(ConcentrateState)
graph.add_node('validate', validate_quality)
graph.add_node('logistics', process_shipment)
graph.add_edge('validate', 'logistics')
graph.add_edge('logistics', END)
graph.set_entry_point('validate')
graph = graph.compile()
