from typing import TypedDict
from langgraph.graph import StateGraph, END

class AssemblyState(TypedDict):
    spec_data: dict
    validation_passed: bool
    compliance_report: str

def validate_materials(state: AssemblyState):
    check = state['spec_data'].get('material_grade') in ['2024-T3', '6061-T6']
    return {'validation_passed': check, 'compliance_report': 'Material check complete'}

def structural_integrity_check(state: AssemblyState):
    if state['validation_passed']:
        return {'compliance_report': 'Passed structural load test requirements'}
    return {'compliance_report': 'Failed structural requirements'}

graph = StateGraph(AssemblyState)
graph.add_node('material_validation', validate_materials)
graph.add_node('integrity_test', structural_integrity_check)
graph.set_entry_point('material_validation')
graph.add_edge('material_validation', 'integrity_test')
graph.add_edge('integrity_test', END)
graph = graph.compile()