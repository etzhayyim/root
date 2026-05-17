from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class ProcurementState(TypedDict):
    component_id: str
    specs: dict
    validated: bool
    compliance_report: str

def validate_material_specs(state: ProcurementState):
    # Business logic for SS component validation
    grade = state['specs'].get('grade')
    state['validated'] = grade in ['304', '316', '316L']
    return state

def generate_compliance(state: ProcurementState):
    state['compliance_report'] = 'Grade verified and tensile test docs attached' if state['validated'] else 'Verification failed'
    return state

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_material_specs)
graph.add_node('compliance', generate_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()