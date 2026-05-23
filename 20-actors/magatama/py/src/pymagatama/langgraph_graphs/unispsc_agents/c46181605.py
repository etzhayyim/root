from typing import TypedDict
from langgraph.graph import StateGraph, END

class SafetyShoeState(TypedDict):
    spec_data: dict
    validated: bool
    compliance_report: str

def validate_compliance(state: SafetyShoeState):
    standard = state['spec_data'].get('standard')
    validated = bool(standard in ['JIS T8101', 'EN ISO 20345'])
    return {'validated': validated, 'compliance_report': 'Compliant' if validated else 'Non-compliant'}

graph = StateGraph(SafetyShoeState)
graph.add_node('validate', validate_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
