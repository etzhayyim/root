from typing import TypedDict
from langgraph.graph import StateGraph, END

class PumpState(TypedDict):
    flow_rate: float
    tubing_material: str
    validation_passed: bool

def validate_spec(state: PumpState):
    state['validation_passed'] = state['flow_rate'] > 0 and state['tubing_material'] is not None
    return state

def route_by_validation(state: PumpState):
    return 'process' if state['validation_passed'] else END

graph = StateGraph(PumpState)
graph.add_node('validate', validate_spec)
graph.add_edge('validate', 'process')
graph.add_node('process', lambda x: x)
graph.add_edge('process', END)
graph.set_entry_point('validate')
graph = graph.compile()