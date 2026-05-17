from typing import TypedDict
from langgraph.graph import StateGraph, END

class SafetySystemState(TypedDict):
    specs: dict
    validation_passed: bool
    compliance_report: str

def validate_specs(state: SafetySystemState):
    # Business logic for isolation system verification
    rating = state['specs'].get('explosion_proof_rating', 'none')
    state['validation_passed'] = rating != 'none'
    return {'validation_passed': state['validation_passed']}

def generate_compliance_report(state: SafetySystemState):
    state['compliance_report'] = 'IEC Compliant' if state['validation_passed'] else 'Non-Compliant'
    return {'compliance_report': state['compliance_report']}

graph = StateGraph(SafetySystemState)
graph.add_node('validator', validate_specs)
graph.add_node('reporter', generate_compliance_report)
graph.set_entry_point('validator')
graph.add_edge('validator', 'reporter')
graph.add_edge('reporter', END)
graph = graph.compile()