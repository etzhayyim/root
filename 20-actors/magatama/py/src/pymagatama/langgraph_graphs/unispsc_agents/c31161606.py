from typing import TypedDict
from langgraph.graph import StateGraph, END

class DoorBoltState(TypedDict):
    spec_data: dict
    validation_result: bool

def validate_bolt_spec(state: DoorBoltState):
    specs = state['spec_data']
    valid = 'material' in specs and 'dimensions' in specs
    return {'validation_result': valid}

def route_by_validation(state: DoorBoltState):
    return 'valid' if state['validation_result'] else 'invalid'

graph = StateGraph(DoorBoltState)
graph.add_node('validate', validate_bolt_spec)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph.compile()