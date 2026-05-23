from typing import TypedDict
from langgraph.graph import StateGraph, END

class CAPDState(TypedDict):
    spec_sheet: str
    validation_status: str
    compliance_passed: bool

def validate_sterilization(state: CAPDState):
    # Simulate validation logic for medical device sterility specs
    state['validation_status'] = 'COMPLIANT' if 'ISO' in state['spec_sheet'] else 'FAIL'
    state['compliance_passed'] = state['validation_status'] == 'COMPLIANT'
    return state

graph = StateGraph(CAPDState)
graph.add_node('validate_sterilization', validate_sterilization)
graph.set_entry_point('validate_sterilization')
graph.add_edge('validate_sterilization', END)
graph = graph.compile()
