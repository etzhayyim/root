from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class AerospaceState(TypedDict):
    part_number: str
    compliance_docs: List[str]
    validation_passed: bool

def validate_specs(state: AerospaceState):
    # Simulated validation logic for Aerospace Cockpit Indicators
    required = ['AS9100', 'TSO']
    passed = all(cert in state['compliance_docs'] for cert in required)
    return {'validation_passed': passed}

def route_verification(state: AerospaceState):
    return 'approved' if state['validation_passed'] else 'rejected'

graph = StateGraph(AerospaceState)
graph.add_node('validate', validate_specs)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
graph = graph.compile()