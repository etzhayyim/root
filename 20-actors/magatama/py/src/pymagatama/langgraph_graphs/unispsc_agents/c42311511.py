from typing import TypedDict
from langgraph.graph import StateGraph, END

class BandageState(TypedDict):
    spec_data: dict
    validated: bool
    compliance_report: str

def validate_medical_grade(state: BandageState):
    if state['spec_data'].get('sterility_status') == 'certified':
        return {'validated': True, 'compliance_report': 'Safety standards met.'}
    return {'validated': False, 'compliance_report': 'Missing sterility cert.'}

graph = StateGraph(BandageState)
graph.add_node('validate', validate_medical_grade)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()