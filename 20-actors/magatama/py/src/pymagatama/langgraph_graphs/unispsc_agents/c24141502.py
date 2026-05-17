from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ShrinkWrapState(TypedDict):
    thickness: float
    shrink_ratio: float
    material: str
    is_compliant: bool

def validate_specs(state: ShrinkWrapState):
    state['is_compliant'] = state['thickness'] >= 15 and state['shrink_ratio'] >= 50
    return state

def route_by_compliance(state: ShrinkWrapState):
    return 'compliant' if state['is_compliant'] else 'non_compliant'

graph = StateGraph(ShrinkWrapState)
graph.add_node('validate', validate_specs)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
graph = graph.compile()