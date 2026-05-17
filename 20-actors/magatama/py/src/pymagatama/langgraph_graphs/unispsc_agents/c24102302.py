from typing import TypedDict
from langgraph.graph import StateGraph, END

class AGVState(TypedDict):
    specs: dict
    validation_result: bool
    route_validated: bool

def validate_specs(state: AGVState):
    state['validation_result'] = 'load_capacity_kg' in state['specs']
    return state

def validate_path(state: AGVState):
    state['route_validated'] = state['specs'].get('operating_environment_conditions', False)
    return state

graph = StateGraph(AGVState)
graph.add_node('validate_specs', validate_specs)
graph.add_node('validate_path', validate_path)
graph.set_entry_point('validate_specs')
graph.add_edge('validate_specs', 'validate_path')
graph.add_edge('validate_path', END)