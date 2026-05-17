from typing import TypedDict
from langgraph.graph import StateGraph, END

class ComponentState(TypedDict):
    specs: dict
    approved: bool

def validate_specs(state: ComponentState):
    required = ['Material Grade', 'Dimensional Tolerance']
    state['approved'] = all(k in state['specs'] for k in required)
    return state

def route_verification(state: ComponentState):
    return 'process' if state['approved'] else END

graph = StateGraph(ComponentState)
graph.add_node('validate', validate_specs)
graph.add_node('process', lambda x: x)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_verification)
graph.add_edge('process', END)
graph = graph.compile()