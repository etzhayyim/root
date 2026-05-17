from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class AirwayState(TypedDict):
    product_specs: dict
    validation_passed: bool
    compliance_report: str

def validate_medical_compliance(state: AirwayState):
    specs = state['product_specs']
    passed = 'FDA' in specs.get('certifications', []) and specs.get('is_sterile', False)
    return {'validation_passed': passed, 'compliance_report': 'Validated' if passed else 'Failed'}

def finalize_procurement_data(state: AirwayState):
    return {'compliance_report': f'Procurement Ready: {state["compliance_report"]}'}

graph = StateGraph(AirwayState)
graph.add_node('validate', validate_medical_compliance)
graph.add_node('finalize', finalize_procurement_data)
graph.set_entry_point('validate')
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph = graph.compile()