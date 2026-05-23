from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class HeatShieldState(TypedDict):
    specs: dict
    validation_passed: bool
    compliance_report: List[str]

def validate_material_specs(state: HeatShieldState):
    # Simulate thermal property validation against aerospace standards
    state['validation_passed'] = state['specs'].get('melting_point', 0) > 1000
    return {'validation_passed': state['validation_passed']}

def export_review_check(state: HeatShieldState):
    # Dual-use export control routing logic
    report = ['Standard engineering review complete']
    if state['specs'].get('is_military_grade'):
        report.append('FLAG: Dual-use export control review required')
    return {'compliance_report': report}

graph = StateGraph(HeatShieldState)
graph.add_node('validate', validate_material_specs)
graph.add_node('compliance', export_review_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
