from typing import TypedDict
from langgraph.graph import StateGraph, END

class ArmorState(TypedDict):
    spec_data: dict
    validation_status: str
    compliance_risk: float

def validate_ballistics(state: ArmorState):
    standard = state['spec_data'].get('Ballistic_Certification_Standard')
    status = 'approved' if standard in ['NIJ_Level_III', 'NIJ_Level_IV'] else 'rejected'
    return {'validation_status': status}

def check_export_compliance(state: ArmorState):
    return {'compliance_risk': 0.9 if state['validation_status'] == 'approved' else 0.0}

graph = StateGraph(ArmorState)
graph.add_node('validate', validate_ballistics)
graph.add_node('check_export', check_export_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'check_export')
graph.add_edge('check_export', END)
graph = graph.compile()