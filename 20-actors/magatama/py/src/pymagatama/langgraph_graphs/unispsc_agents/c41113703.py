from typing import TypedDict
from langgraph.graph import StateGraph, END

class CouplerState(TypedDict):
    specs: dict
    validated: bool
    compliance_check: str

def validate_specs(state: CouplerState):
    required = ['Frequency Range', 'Coupling Factor', 'Insertion Loss']
    valid = all(k in state['specs'] for k in required)
    return {'validated': valid, 'compliance_check': 'PASS' if valid else 'FAIL'}

def export_review(state: CouplerState):
    if state['validated'] and state['specs'].get('Frequency Range', 0) > 10e9:
        return {'compliance_check': 'EXPORT_CONTROL_REQUIRED'}
    return {'compliance_check': 'CLEAR'}

graph = StateGraph(CouplerState)
graph.add_node('validate', validate_specs)
graph.add_node('export', export_review)
graph.set_entry_point('validate')
graph.add_edge('validate', 'export')
graph.add_edge('export', END)
graph = graph.compile()