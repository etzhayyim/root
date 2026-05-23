from typing import TypedDict
from langgraph.graph import StateGraph, END

class SurgicalKitState(TypedDict):
    kit_id: str
    compliance_checked: bool
    sterilization_verified: bool

def validate_specs(state: SurgicalKitState):
    state['compliance_checked'] = True
    return 'check_sterilization'

def verify_sterilization(state: SurgicalKitState):
    state['sterilization_verified'] = True
    return END

graph = StateGraph(SurgicalKitState)
graph.add_node('validate', validate_specs)
graph.add_node('check_sterilization', verify_sterilization)
graph.set_entry_point('validate')
graph.add_edge('validate', 'check_sterilization')
graph.add_edge('check_sterilization', END)
graph = graph.compile()
