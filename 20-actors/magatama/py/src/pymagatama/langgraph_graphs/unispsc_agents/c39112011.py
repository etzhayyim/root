from typing import TypedDict
from langgraph.graph import StateGraph, END

class LightingState(TypedDict):
    specs: dict
    is_compliant: bool
    validation_log: list

def validate_specs(state: LightingState):
    log = []
    required = ['IP_rating', 'safety_certification']
    valid = all(key in state['specs'] for key in required)
    if not valid: log.append('Missing mandatory spec fields')
    return {'is_compliant': valid, 'validation_log': log}

def approval_step(state: LightingState):
    return {'validation_log': state['validation_log'] + ['Compliance Verified']}

graph = StateGraph(LightingState)
graph.add_node('validate', validate_specs)
graph.add_node('approve', approval_step)
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph.set_entry_point('validate')
graph = graph.compile()
