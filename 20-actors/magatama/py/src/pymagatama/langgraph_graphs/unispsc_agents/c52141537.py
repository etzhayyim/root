from langgraph.graph import StateGraph, END
from typing import TypedDict

class CookerState(TypedDict):
    spec_data: dict
    is_compliant: bool

def validate_specs(state: CookerState):
    required = ['voltage', 'capacity', 'safety_cert']
    passed = all(k in state['spec_data'] for k in required)
    return {'is_compliant': passed}

def approval_check(state: CookerState):
    return 'approved' if state['is_compliant'] else 'rejected'

graph = StateGraph(CookerState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph.compile()