from typing import TypedDict, Annotated
import operator
from langgraph.graph import StateGraph, END

class RackState(TypedDict):
    specifications: dict
    validation_errors: Annotated[list, operator.add]
    is_compliant: bool

def validate_load_capacity(state: RackState):
    capacity = state['specifications'].get('load_capacity', 0)
    if capacity < 500:
        return {'validation_errors': ['Load capacity too low for server density']}
    return {'validation_errors': []}

def check_dimensions(state: RackState):
    if state['specifications'].get('depth', 0) < 800:
        return {'validation_errors': ['Insufficient depth for modern blade servers']}
    return {'validation_errors': []}

graph = StateGraph(RackState)
graph.add_node('load_check', validate_load_capacity)
graph.add_node('dim_check', check_dimensions)
graph.set_entry_point('load_check')
graph.add_edge('load_check', 'dim_check')
graph.add_edge('dim_check', END)
app = graph.compile()