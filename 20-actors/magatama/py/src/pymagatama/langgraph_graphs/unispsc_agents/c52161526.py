from typing import TypedDict
from langgraph.graph import StateGraph, END

class SatelliteState(TypedDict):
    signal_frequency: float
    encryption_type: str
    compliance_check: bool

def validate_specs(state: SatelliteState):
    state['compliance_check'] = state['signal_frequency'] > 1.0
    return state

graph = StateGraph(SatelliteState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()