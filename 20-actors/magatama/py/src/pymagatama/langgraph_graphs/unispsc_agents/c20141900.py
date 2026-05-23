from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class RackingState(TypedDict):
    specs: dict
    approved: bool
    validation_log: List[str]

def validate_load_capacity(state: RackingState):
    capacity = state['specs'].get('load_capacity', 0)
    if capacity > 0:
        state['validation_log'].append('Capacity valid')
    return state

def check_compliance(state: RackingState):
    state['approved'] = state['specs'].get('seismic_certified', False)
    return state

graph = StateGraph(RackingState)
graph.add_node('validate', validate_load_capacity)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
