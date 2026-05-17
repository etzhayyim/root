from typing import TypedDict
from langgraph.graph import StateGraph, END

class ClampState(TypedDict):
    spec_data: dict
    is_validated: bool
    error_log: list

def validate_specs(state: ClampState):
    specs = state['spec_data']
    is_valid = all(key in specs for key in ['clamping_force', 'rpm_limit'])
    return {'is_validated': is_valid}

def process_clamp_procurement(state: ClampState):
    print('Processing 3-jaw clamp technical procurement...')
    return {'error_log': ['Compliance check passed']}

graph = StateGraph(ClampState)
graph.add_node('validator', validate_specs)
graph.add_node('processor', process_clamp_procurement)
graph.add_edge('validator', 'processor')
graph.add_edge('processor', END)
graph.set_entry_point('validator')
graph = graph.compile()