from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class SensorProcurementState(TypedDict):
    specs: dict
    validation_passed: bool
    compliance_report: str

def validate_specs(state: SensorProcurementState):
    required_keys = ['voltage', 'range', 'ip_rating']
    passed = all(k in state['specs'] for k in required_keys)
    return {'validation_passed': passed}

def check_dual_use(state: SensorProcurementState):
    report = 'Reviewing against dual-use control lists' if state['validation_passed'] else 'Invalid'
    return {'compliance_report': report}

graph = StateGraph(SensorProcurementState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_dual_use)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
