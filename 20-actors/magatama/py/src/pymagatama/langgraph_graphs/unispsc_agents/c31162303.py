from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END

class MountingBarState(TypedDict):
    spec_data: dict
    validation_passed: bool

def validate_specs(state: MountingBarState):
    required = ['material', 'length', 'finish']
    passed = all(k in state['spec_data'] for k in required)
    return {'validation_passed': passed}

def route_by_validation(state: MountingBarState):
    return 'validate' if not state.get('validation_passed') else END

graph = StateGraph(MountingBarState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
