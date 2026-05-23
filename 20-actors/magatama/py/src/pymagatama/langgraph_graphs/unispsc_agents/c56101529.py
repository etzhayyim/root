from typing import TypedDict
from langgraph.graph import StateGraph, END

class RackState(TypedDict):
    dimension_check: bool
    material_compliance: bool
    is_approved: bool

def validate_specs(state: RackState):
    state['is_approved'] = state['dimension_check'] and state['material_compliance']
    return state

graph = StateGraph(RackState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
