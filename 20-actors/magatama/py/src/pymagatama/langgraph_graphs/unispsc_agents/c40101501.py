from typing import TypedDict
from langgraph.graph import StateGraph, END

class AirCollectorState(TypedDict):
    pressure_req: float
    flow_rate: float
    is_compliant: bool

def validate_specs(state: AirCollectorState):
    state['is_compliant'] = state['pressure_req'] > 0 and state['flow_rate'] > 0
    return state

def route_verification(state: AirCollectorState):
    return 'verified' if state['is_compliant'] else 'failed'

graph = StateGraph(AirCollectorState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph.compile()
