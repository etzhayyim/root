from typing import TypedDict
from langgraph.graph import StateGraph, END

class MotorSpecState(TypedDict):
    voltage: float
    power_kw: float
    ip_rating: str
    is_compliant: bool

def validate_specs(state: MotorSpecState):
    if state['power_kw'] > 0 and state['voltage'] >= 12:
        return {'is_compliant': True}
    return {'is_compliant': False}

graph = StateGraph(MotorSpecState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()