from typing import TypedDict
from langgraph.graph import StateGraph, END

class HubState(TypedDict):
    specs: dict
    validation_passed: bool

def validate_engineering_specs(state: HubState):
    required = ['tolerance', 'material', 'load_rating']
    passed = all(k in state['specs'] for k in required)
    return {'validation_passed': passed}

def route_by_validation(state: HubState):
    return 'passed' if state['validation_passed'] else 'failed'

graph_builder = StateGraph(HubState)
graph_builder.add_node('validate', validate_engineering_specs)
graph_builder.add_edge('validate', END)
graph_builder.set_entry_point('validate')
graph = graph_builder.compile()
