from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END

class LightingState(TypedDict):
    spec_data: dict
    validation_passed: bool
    log: list[str]

def validate_specs(state: LightingState):
    specs = state['spec_data']
    passed = 'Guide Number' in specs and 'Color Temperature' in specs
    return {'validation_passed': passed, 'log': ['Specs validated'] if passed else ['Missing technical fields']}

def approval_check(state: LightingState):
    return 'APPROVED' if state['validation_passed'] else 'REJECTED'

graph = StateGraph(LightingState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph.compile()