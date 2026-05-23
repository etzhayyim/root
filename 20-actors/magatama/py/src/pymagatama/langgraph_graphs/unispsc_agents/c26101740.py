from typing import TypedDict, Annotated, Sequence
from langgraph.graph import StateGraph, END

class InjectorState(TypedDict):
    specs: dict
    validation_passed: bool
    log: list

def validate_specs(state: InjectorState):
    required = ['flow_rate', 'pressure']
    passed = all(k in state['specs'] for k in required)
    return {'validation_passed': passed, 'log': ['Specs validated: ' + str(passed)]}

def route_verification(state: InjectorState):
    return 'validate' if not state['validation_passed'] else END

graph = StateGraph(InjectorState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
