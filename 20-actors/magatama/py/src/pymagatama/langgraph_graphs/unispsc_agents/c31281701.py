from typing import TypedDict
from langgraph.graph import StateGraph, END

class WeldState(TypedDict):
    spec_data: dict
    inspection_result: bool

def validate_welding_specs(state: WeldState):
    # Business logic for weld certification check
    wps = state['spec_data'].get('wps_code')
    return {'inspection_result': wps is not None}

def approval_node(state: WeldState):
    return {'inspection_result': True}

graph = StateGraph(WeldState)
graph.add_node('validate', validate_welding_specs)
graph.add_node('approve', approval_node)
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph.set_entry_point('validate')
graph = graph.compile()