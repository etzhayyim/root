from typing import TypedDict
from langgraph.graph import StateGraph, END

class MorgueState(TypedDict):
    temp_celsius: float
    capacity: int
    is_compliant: bool

def validate_specs(state: MorgueState):
    if state['temp_celsius'] <= -18.0 and state['capacity'] > 0:
        return {'is_compliant': True}
    return {'is_compliant': False}

graph = StateGraph(MorgueState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
