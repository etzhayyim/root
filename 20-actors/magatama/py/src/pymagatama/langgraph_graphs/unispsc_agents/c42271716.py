from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class InsufflatorCaseState(TypedDict):
    case_model: str
    material_specs: dict
    compliance_passed: bool
    inspection_report: List[str]

def validate_material(state: InsufflatorCaseState):
    passed = state['material_specs'].get('biocompatible', False)
    return {'compliance_passed': passed}

def generate_report(state: InsufflatorCaseState):
    status = 'PASS' if state['compliance_passed'] else 'FAIL'
    return {'inspection_report': [f'Material validation: {status}']}

graph = StateGraph(InsufflatorCaseState)
graph.add_node('validate', validate_material)
graph.add_node('report', generate_report)
graph.add_edge('validate', 'report')
graph.add_edge('report', END)
graph.set_entry_point('validate')
graph = graph.compile()
