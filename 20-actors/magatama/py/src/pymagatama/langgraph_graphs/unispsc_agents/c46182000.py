from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class RespiratoryState(TypedDict):
    item_name: str
    compliance_cert: str
    filter_rating: str
    is_approved: bool

def validate_certification(state: RespiratoryState):
    if state['compliance_cert'] in ['NIOSH', 'N95', 'FFP2', 'FFP3']:
        return {'is_approved': True}
    return {'is_approved': False}

workflow = StateGraph(RespiratoryState)
workflow.add_node('cert_validation', validate_certification)
workflow.set_entry_point('cert_validation')
workflow.add_edge('cert_validation', END)
graph = workflow.compile()