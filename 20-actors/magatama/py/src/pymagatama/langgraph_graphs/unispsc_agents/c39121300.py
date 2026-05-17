from typing import TypedDict
from langgraph.graph import StateGraph, END

class EnclosureState(TypedDict):
    spec_requirements: dict
    compliance_check: bool
    approved: bool

def validate_specs(state: EnclosureState):
    # Business logic for electrical fitting compliance validation
    is_compliant = 'ip_rating' in state['spec_requirements'] and 'material' in state['spec_requirements']
    return {'compliance_check': is_compliant}

def approval_check(state: EnclosureState):
    return {'approved': state['compliance_check']}

graph = StateGraph(EnclosureState)
graph.add_node('validate', validate_specs)
graph.add_node('approve', approval_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
compile_graph = graph.compile()