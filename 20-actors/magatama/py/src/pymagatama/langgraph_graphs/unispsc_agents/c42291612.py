from typing import TypedDict
from langgraph.graph import StateGraph, END

class SurgicalRongeurState(TypedDict):
    spec_sheet: dict
    validation_status: bool
    compliance_report: str

def validate_medical_grade(state: SurgicalRongeurState):
    material = state['spec_sheet'].get('material', '')
    is_valid = material == 'Surgical Stainless Steel'
    return {'validation_status': is_valid, 'compliance_report': 'Material check passed' if is_valid else 'Invalid material'}

def process_sterilization_flow(state: SurgicalRongeurState):
    if state['validation_status']:
        return {'compliance_report': 'Ready for sterilization validation'}
    return {'compliance_report': 'Rejected due to material non-compliance'}

graph = StateGraph(SurgicalRongeurState)
graph.add_node('validate', validate_medical_grade)
graph.add_node('sterilize', process_sterilization_flow)
graph.add_edge('validate', 'sterilize')
graph.add_edge('sterilize', END)
graph.set_entry_point('validate')
rongeur_graph = graph.compile()
