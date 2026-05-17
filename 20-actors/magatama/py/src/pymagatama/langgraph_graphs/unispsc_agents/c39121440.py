from typing import TypedDict
from langgraph.graph import StateGraph, END

class CableState(TypedDict):
    voltage: int
    current: int
    certified: bool
    approved: bool

def validate_specs(state: CableState):
    state['approved'] = state['voltage'] >= 110 and state['certified'] == True
    return state

graph = StateGraph(CableState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()