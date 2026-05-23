from typing import TypedDict
from langgraph.graph import StateGraph, END

class OvenState(TypedDict):
    specs: dict
    approved: bool
    validation_log: list

def validate_specs(state: OvenState):
    log = []
    required = ['Voltage', 'Capacity', 'Certification']
    approved = all(k in state['specs'] for k in required)
    if not approved: log.append('Missing mandatory fields.')
    return {'approved': approved, 'validation_log': log}

def approval_check(state: OvenState):
    return 'approved' if state['approved'] else 'rejected'

graph = StateGraph(OvenState)
graph.add_node('validate', validate_specs)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
graph = graph.compile()
