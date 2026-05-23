from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class SurgicalState(TypedDict):
    device_id: str
    compliance_status: bool
    sterilization_verified: bool

def validate_compliance(state: SurgicalState):
    print(f'Checking compliance for {state['device_id']}')
    return {'compliance_status': True}

def verify_sterilization(state: SurgicalState):
    print(f'Verifying sterilization for {state['device_id']}')
    return {'sterilization_verified': True}

graph = StateGraph(SurgicalState)
graph.add_node('validate', validate_compliance)
graph.add_node('sterilize', verify_sterilization)
graph.set_entry_point('validate')
graph.add_edge('validate', 'sterilize')
graph.add_edge('sterilize', END)
graph = graph.compile()
