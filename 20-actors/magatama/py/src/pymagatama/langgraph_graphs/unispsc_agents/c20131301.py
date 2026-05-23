from typing import TypedDict
from langgraph.graph import StateGraph, END

class AbrasiveState(TypedDict):
    spec_data: dict
    validated: bool

def validate_specs(state: AbrasiveState):
    required = ['grit_size', 'hardness_rating']
    state['validated'] = all(k in state['spec_data'] for k in required)
    return state

def check_speed_safety(state: AbrasiveState):
    speed = state['spec_data'].get('maximum_operating_speed', 0)
    if speed > 15000: state['validated'] = False
    return state

graph = StateGraph(AbrasiveState)
graph.add_node('validate', validate_specs)
graph.add_node('safety_check', check_speed_safety)
graph.set_entry_point('validate')
graph.add_edge('validate', 'safety_check')
graph.add_edge('safety_check', END)
graph = graph.compile()
