from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class PDAProcessState(TypedDict):
    device_specs: dict
    compliance_check: bool
    approved: bool

def validate_specs(state: PDAProcessState):
    required = ['OS', 'Security_Standard']
    valid = all(k in state['device_specs'] for k in required)
    return {'compliance_check': valid}

def approval_step(state: PDAProcessState):
    return {'approved': state['compliance_check']}

graph = StateGraph(PDAProcessState)
graph.add_node('validate', validate_specs)
graph.add_node('approve', approval_step)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph = graph.compile()
