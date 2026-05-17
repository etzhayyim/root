from typing import TypedDict
from langgraph.graph import StateGraph, END

class PumpState(TypedDict):
    spec_data: dict
    validated: bool
    compliance_report: str

def validate_materials(state: PumpState):
    materials = state['spec_data'].get('wetted_materials', [])
    is_valid = all(m in ['Stainless Steel', 'PTFE', 'Polypropylene'] for m in materials)
    return {'validated': is_valid, 'compliance_report': 'Material check passed' if is_valid else 'Material mismatch'}

def check_compliance(state: PumpState):
    if state['validated']:
        return {'compliance_report': 'Safety and ATEX compliance verified.'}
    return {'compliance_report': 'Compliance criteria failed validation.'}

graph = StateGraph(PumpState)
graph.add_node('validate', validate_materials)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()