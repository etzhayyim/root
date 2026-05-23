from typing import TypedDict
from langgraph.graph import StateGraph, END

class DockingState(TypedDict):
    model_info: dict
    compatibility_check: bool
    approved: bool

def validate_specs(state: DockingState):
    # Business logic for confirming power and port requirements
    state['compatibility_check'] = state['model_info'].get('power_delivery', 0) >= 65
    state['approved'] = state['compatibility_check']
    return state

graph = StateGraph(DockingState)
graph.add_node('validate_specs', validate_specs)
graph.set_entry_point('validate_specs')
graph.add_edge('validate_specs', END)
graph = graph.compile()
