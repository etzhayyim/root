from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ShimState(TypedDict):
    thickness: float
    material: str
    compliance_check: bool

def validate_shim_spec(state: ShimState):
    state['compliance_check'] = state['thickness'] > 0 and state['material'] == 'brass'
    return state

graph = StateGraph(ShimState)
graph.add_node('validate', validate_shim_spec)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()