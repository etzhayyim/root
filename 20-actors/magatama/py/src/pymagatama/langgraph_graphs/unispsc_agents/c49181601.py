from typing import TypedDict
from langgraph.graph import StateGraph, END

class TargetState(TypedDict):
    spec_data: dict
    is_compliant: bool

def validate_durability(state: TargetState):
    density = state['spec_data'].get('density', 0)
    state['is_compliant'] = density > 45
    return state

def check_standards(state: TargetState):
    if state['is_compliant']:
        state['is_compliant'] = state['spec_data'].get('world_archery_certified', False)
    return state

graph = StateGraph(TargetState)
graph.add_node('validate', validate_durability)
graph.add_node('standards', check_standards)
graph.set_entry_point('validate')
graph.add_edge('validate', 'standards')
graph.add_edge('standards', END)
graph = graph.compile()
