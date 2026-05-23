from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class CastState(TypedDict):
    part_specs: dict
    validation_passed: bool
    compliance_risk: List[str]

def validate_specs(state: CastState):
    required = ['material', 'tolerance', 'ndt_report']
    passed = all(k in state['part_specs'] for k in required)
    return {'validation_passed': passed}

def check_compliance(state: CastState):
    compliance = ['export_control_check'] if 'high_alloy' in state['part_specs'].get('material', '') else []
    return {'compliance_risk': compliance}

graph = StateGraph(CastState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
