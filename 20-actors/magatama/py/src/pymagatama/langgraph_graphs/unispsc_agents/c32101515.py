from typing import TypedDict
from langgraph.graph import StateGraph, END

class AttenuatorState(TypedDict):
    specs: dict
    validated: bool
    compliance_check: bool

def validate_specs(state: AttenuatorState):
    s = state['specs']
    valid = all(key in s for key in ['frequency', 'attenuation', 'power'])
    return {'validated': valid}

def check_compliance(state: AttenuatorState):
    return {'compliance_check': True}

graph = StateGraph(AttenuatorState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()