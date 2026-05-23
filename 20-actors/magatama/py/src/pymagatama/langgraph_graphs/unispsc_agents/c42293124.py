from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class NerveRetractorState(TypedDict):
    spec_data: dict
    validation_passed: bool
    compliance_report: str

def validate_material(state: NerveRetractorState):
    material = state['spec_data'].get('material')
    is_valid = material in ['Stainless Steel 316L', 'Titanium Grade 5']
    return {'validation_passed': is_valid}

def process_compliance(state: NerveRetractorState):
    report = 'ISO 13485 requirements met' if state['validation_passed'] else 'Compliance failure'
    return {'compliance_report': report}

graph = StateGraph(NerveRetractorState)
graph.add_node('validate', validate_material)
graph.add_node('compliance', process_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
