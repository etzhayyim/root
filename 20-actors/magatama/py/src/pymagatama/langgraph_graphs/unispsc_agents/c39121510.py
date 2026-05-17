from typing import TypedDict
from langgraph.graph import StateGraph, END
class SwitchState(TypedDict):
    specs: dict
    approved: bool
def validate_specs(state: SwitchState):
    required = ['voltage', 'current', 'ip_rating']
    state['approved'] = all(k in state['specs'] for k in required)
    return state
def route_by_validation(state: SwitchState):
    return 'process' if state['approved'] else END
graph = StateGraph(SwitchState)
graph.add_node('validate', validate_specs)
graph.add_node('process', lambda s: s)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_validation)
graph.add_edge('process', END)
graph = graph.compile()