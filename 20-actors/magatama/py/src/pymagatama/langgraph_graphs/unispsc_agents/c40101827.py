from typing import TypedDict
from langgraph.graph import StateGraph, END

class HeaterSpecState(TypedDict):
    temp_max: float
    has_certification: bool
    is_compliant: bool

def validate_specs(state: HeaterSpecState):
    compliant = state['temp_max'] >= 1000 and state['has_certification']
    return {'is_compliant': compliant}

graph = StateGraph(HeaterSpecState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()