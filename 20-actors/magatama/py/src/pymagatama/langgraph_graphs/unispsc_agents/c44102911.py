from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class OfficeSupplyState(TypedDict):
    product_id: str
    specifications: dict
    validation_passed: bool
    compliance_report: str

def validate_safety_data(state: OfficeSupplyState):
    sds_info = state['specifications'].get('sds_available', False)
    return {'validation_passed': sds_info, 'compliance_report': 'SDS Checked' if sds_info else 'SDS Missing'}

def audit_specifications(state: OfficeSupplyState):
    is_lint_free = state['specifications'].get('is_lint_free', True)
    return {'validation_passed': state['validation_passed'] and is_lint_free}

graph = StateGraph(OfficeSupplyState)
graph.add_node('validate_sds', validate_safety_data)
graph.add_node('check_specs', audit_specifications)
graph.set_entry_point('validate_sds')
graph.add_edge('validate_sds', 'check_specs')
graph.add_edge('check_specs', END)

compiled_graph = graph.compile()