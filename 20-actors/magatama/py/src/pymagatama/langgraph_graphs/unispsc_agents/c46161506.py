from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    material_data: dict
    validation_passed: bool
    compliance_risk: str

def validate_safety_compliance(state: ProcurementState):
    sds = state['material_data'].get('sds')
    composition = state['material_data'].get('composition')
    is_valid = bool(sds and composition)
    return {'validation_passed': is_valid}

def assess_risk(state: ProcurementState):
    risk = 'HIGH' if state['material_data'].get('toxic_content', True) else 'LOW'
    return {'compliance_risk': risk}

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_safety_compliance)
graph.add_node('risk_assessment', assess_risk)
graph.set_entry_point('validate')
graph.add_edge('validate', 'risk_assessment')
graph.add_edge('risk_assessment', END)
graph = graph.compile()