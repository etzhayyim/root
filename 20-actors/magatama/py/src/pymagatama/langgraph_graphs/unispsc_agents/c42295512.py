from typing import TypedDict
from langgraph.graph import StateGraph, END

class ShuntState(TypedDict):
    spec_data: dict
    validation_status: bool
    compliance_report: str

def validate_biocompatibility(state: ShuntState):
    compliance = state['spec_data'].get('iso10993', False)
    return {'validation_status': compliance, 'compliance_report': 'Passed' if compliance else 'Failed'}

def approval_node(state: ShuntState):
    return {'compliance_report': 'Awaiting Regulatory Review'}

graph = StateGraph(ShuntState)
graph.add_node('validate', validate_biocompatibility)
graph.add_node('approve', approval_node)
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph.set_entry_point('validate')