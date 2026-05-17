from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class PackageStopState(TypedDict):
    part_number: str
    spec_compliance: bool
    validation_log: List[str]

def validate_load_capacity(state: PackageStopState):
    # Simulate CAD/Spec validation logic
    state['spec_compliance'] = True
    state['validation_log'].append('Load capacity validated against ISO standards.')
    return state

def check_dimensions(state: PackageStopState):
    state['validation_log'].append('Dimensions verified for standard mounting.')
    return state

graph = StateGraph(PackageStopState)
graph.add_node('load_check', validate_load_capacity)
graph.add_node('dim_check', check_dimensions)
graph.set_entry_point('load_check')
graph.add_edge('load_check', 'dim_check')
graph.add_edge('dim_check', END)
graph = graph.compile()