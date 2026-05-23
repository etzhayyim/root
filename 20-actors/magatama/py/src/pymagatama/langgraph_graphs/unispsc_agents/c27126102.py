from typing import TypedDict
from langgraph.graph import StateGraph, END

class AccumulatorState(TypedDict):
    pressure_rating: float
    safety_certs: list
    is_compliant: bool

def validate_specs(state: AccumulatorState):
    if state['pressure_rating'] > 350 and 'ASME' not in state['safety_certs']:
        return {'is_compliant': False}
    return {'is_compliant': True}

graph = StateGraph(AccumulatorState)
graph.add_node('validation', validate_specs)
graph.set_entry_point('validation')
graph.add_edge('validation', END)
graph = graph.compile()
