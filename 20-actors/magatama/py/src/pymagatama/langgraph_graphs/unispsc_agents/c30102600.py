from langgraph.graph import StateGraph, END
from typing import TypedDict

class StripProcessingState(TypedDict):
    material_spec: dict
    validation_passed: bool
    error_log: list

def validate_specs(state: StripProcessingState):
    specs = state['material_spec']
    passed = 'thickness' in specs and 'grade' in specs
    return {'validation_passed': passed, 'error_log': [] if passed else ['Missing specifications']}

def route_by_validation(state: StripProcessingState):
    return 'validate' if not state['validation_passed'] else END

graph = StateGraph(StripProcessingState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
