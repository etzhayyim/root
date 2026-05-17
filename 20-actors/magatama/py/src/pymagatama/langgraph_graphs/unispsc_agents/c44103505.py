from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class BindingState(TypedDict):
    material: str
    capacity: int
    is_compliant: bool

def validate_specs(state: BindingState):
    state['is_compliant'] = state['capacity'] > 0 and state['material'] in ['PVC', 'Plastic']
    return state

graph = StateGraph(BindingState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()