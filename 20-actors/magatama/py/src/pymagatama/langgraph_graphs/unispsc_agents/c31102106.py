from typing import TypedDict
from langgraph.graph import StateGraph, END

class CastingState(TypedDict):
    part_specs: dict
    validation_passed: bool
    error_log: list

def validate_specs(state: CastingState):
    specs = state['part_specs']
    passed = 'material' in specs and 'tolerance' in specs
    return {'validation_passed': passed, 'error_log': [] if passed else ['Missing technical specs']}

def conduct_ndt(state: CastingState):
    return {'validation_passed': state['validation_passed']}

graph = StateGraph(CastingState)
graph.add_node('validate', validate_specs)
graph.add_node('ndt_inspect', conduct_ndt)
graph.add_edge('validate', 'ndt_inspect')
graph.add_edge('ndt_inspect', END)
graph.set_entry_point('validate')
graph = graph.compile()