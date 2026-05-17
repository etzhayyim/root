from typing import TypedDict
from langgraph.graph import StateGraph, END

class DialysisPumpState(TypedDict):
    pressure_value: float
    flow_rate: float
    is_compliant: bool

def validate_pressure(state: DialysisPumpState):
    state['is_compliant'] = 200 <= state['pressure_value'] <= 500
    return state

def check_flow_stability(state: DialysisPumpState):
    state['is_stable'] = state['flow_rate'] > 0
    return state

graph = StateGraph(DialysisPumpState)
graph.add_node('validate_pressure', validate_pressure)
graph.add_node('check_flow_stability', check_flow_stability)
graph.set_entry_point('validate_pressure')
graph.add_edge('validate_pressure', 'check_flow_stability')
graph.add_edge('check_flow_stability', END)
graph = graph.compile()