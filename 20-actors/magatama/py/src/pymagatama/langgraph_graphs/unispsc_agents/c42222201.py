from typing import TypedDict
from langgraph.graph import StateGraph, END

class InjectionSpecState(TypedDict):
    spec_data: dict
    validated: bool
    compliance_report: str

def validate_medical_standards(state: InjectionSpecState):
    is_compliant = 'iso_certification' in state['spec_data'] and 'regulatory_approval_number' in state['spec_data']
    return {'validated': is_compliant, 'compliance_report': 'Passed' if is_compliant else 'Failed: Missing certifications'}

graph = StateGraph(InjectionSpecState)
graph.add_node('validate', validate_medical_standards)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()