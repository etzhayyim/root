from typing import TypedDict
from langgraph.graph import StateGraph, END

class State(TypedDict):
    facility_type: str
    compliance_checks: list
    design_approved: bool

def validate_facility_specs(state: State):
    state['compliance_checks'].append('Building codes verified')
    return {'compliance_checks': state['compliance_checks']}

def approve_facility(state: State):
    state['design_approved'] = True
    return {'design_approved': True}

graph = StateGraph(State)
graph.add_node('validate', validate_facility_specs)
graph.add_node('approve', approve_facility)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph = graph.compile()
