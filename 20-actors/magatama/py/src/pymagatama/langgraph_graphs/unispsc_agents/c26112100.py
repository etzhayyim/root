from langgraph.graph import StateGraph, END
from typing import TypedDict
class BrakingState(TypedDict):
    spec_data: dict
    approved: bool
def validate_specs(state: BrakingState):
    torque = state['spec_data'].get('torque', 0)
    state['approved'] = torque > 0
    return state
graph = StateGraph(BrakingState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
