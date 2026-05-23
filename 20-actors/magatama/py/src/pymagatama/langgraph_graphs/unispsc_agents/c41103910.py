from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class CentrifugeState(TypedDict):
    material: str
    max_rpm: int
    is_compatible: bool

def validate_specs(state: CentrifugeState):
    state['is_compatible'] = state['max_rpm'] > 1000
    return state

graph = StateGraph(CentrifugeState)
graph.add_node('validate', validate_specs)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
