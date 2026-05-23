from typing import TypedDict
from langgraph.graph import StateGraph, END

class TiltTruckState(TypedDict):
    load_capacity: float
    has_casters: bool
    compliant: bool

def validate_truck_specs(state: TiltTruckState):
    if state['load_capacity'] > 0 and state['has_casters']:
        return {'compliant': True}
    return {'compliant': False}

graph = StateGraph(TiltTruckState)
graph.add_node('validate', validate_truck_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
