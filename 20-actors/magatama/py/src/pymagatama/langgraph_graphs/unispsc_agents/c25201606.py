from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class State(TypedDict):
    part_specs: dict
    validation_passed: bool
    compliance_flags: List[str]

def validate_specs(state: State):
    passed = all(key in state['part_specs'] for key in ['Radiation Hardening Level', 'Pointing Accuracy'])
    return {'validation_passed': passed}

def check_export_control(state: State):
    flags = []
    if state['part_specs'].get('ITAR_restricted', False):
        flags.append('ITAR_REVIEW_REQUIRED')
    return {'compliance_flags': flags}

graph = StateGraph(State)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_export_control)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)

graph = graph.compile()