from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class GravitySpecs(TypedDict):
    accuracy: str
    calibration_status: bool
    compliance_tags: List[str]

def validate_specs(state: GravitySpecs):
    if float(state['accuracy']) < 0.01:
        return {'compliance_tags': state['compliance_tags'] + ['high-precision-verified']}
    return {'compliance_tags': state['compliance_tags'] + ['standard']}

def export_review(state: GravitySpecs):
    return {'compliance_tags': state['compliance_tags'] + ['export-control-check-passed']}

graph = StateGraph(GravitySpecs)
graph.add_node('validate', validate_specs)
graph.add_node('export', export_review)
graph.set_entry_point('validate')
graph.add_edge('validate', 'export')
graph.add_edge('export', END)
graph = graph.compile()