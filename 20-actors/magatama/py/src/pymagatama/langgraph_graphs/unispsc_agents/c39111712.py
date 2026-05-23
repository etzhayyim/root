from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class CanopyState(TypedDict):
    part_number: str
    material_spec: str
    compliance_validated: bool
    final_report: str

def validate_specs(state: CanopyState):
    # Business logic for validating canopy procurement specs
    valid = state.get('material_spec') is not None
    return {'compliance_validated': valid}

def generate_procurement_report(state: CanopyState):
    status = 'approved' if state['compliance_validated'] else 'rejected'
    return {'final_report': f'Procurement for part {state['part_number']} is {status}'}

graph = StateGraph(CanopyState)
graph.add_node('validate', validate_specs)
graph.add_node('report', generate_procurement_report)
graph.add_edge('validate', 'report')
graph.add_edge('report', END)
graph.set_entry_point('validate')
graph = graph.compile()
