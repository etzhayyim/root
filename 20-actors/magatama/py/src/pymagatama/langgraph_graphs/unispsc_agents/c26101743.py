from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class ValveState(TypedDict):
    specs: dict
    validation_passed: bool
    compliance_report: str

def validate_specs(state: ValveState):
    # Simulate geometric verification of engine valve
    tolerance = state['specs'].get('tolerance', 0.05)
    passed = tolerance <= 0.01
    return {'validation_passed': passed}

def check_material_compliance(state: ValveState):
    # Simulate material composition audit
    material = state['specs'].get('material', '')
    return {'compliance_report': 'Material Cert Verified' if material else 'Missing'}

graph = StateGraph(ValveState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_material_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
process = graph.compile()
