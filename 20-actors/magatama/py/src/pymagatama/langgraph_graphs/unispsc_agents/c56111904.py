from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class IndustrialFurnitureState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    approved: bool

def validate_load_capacity(state: IndustrialFurnitureState):
    load = state['spec_data'].get('load_capacity_kg', 0)
    if load < 500:
        state['validation_errors'].append('Load capacity below industrial threshold')
    return state

def check_compliance(state: IndustrialFurnitureState):
    state['approved'] = len(state['validation_errors']) == 0
    return state

graph = StateGraph(IndustrialFurnitureState)
graph.add_node('validate', validate_load_capacity)
graph.add_node('compliance', check_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()
