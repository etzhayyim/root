from typing import TypedDict
from langgraph.graph import StateGraph, END

class FlashlightState(TypedDict):
    lumens: int
    ip_rating: str
    is_compliant: bool

def validate_specs(state: FlashlightState):
    # Business logic for flashlight compliance
    if state['lumens'] > 50 and state['ip_rating'] >= 'IP54':
        return {'is_compliant': True}
    return {'is_compliant': False}

graph = StateGraph(FlashlightState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()