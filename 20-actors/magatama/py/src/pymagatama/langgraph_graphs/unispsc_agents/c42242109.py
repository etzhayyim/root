from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class TractionState(TypedDict):
    spec_requirements: dict
    validation_passed: bool
    compliance_report: str

def validate_materials(state: TractionState):
    # Business logic for confirming medical grade compliance
    state['validation_passed'] = 'ISO-13485' in state['spec_requirements'].get('certs', [])
    return {'validation_passed': state['validation_passed']}

def generate_compliance_report(state: TractionState):
    report = "Validated" if state['validation_passed'] else "Review Needed"
    return {'compliance_report': report}

graph = StateGraph(TractionState)
graph.add_node("validate_materials", validate_materials)
graph.add_node("generate_report", generate_compliance_report)
graph.set_entry_point("validate_materials")
graph.add_edge("validate_materials", "generate_report")
graph.add_edge("generate_report", END)
app = graph.compile()
