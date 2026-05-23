from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class SoftwareState(TypedDict):
    license_key: str
    validation_checks: List[str]
    is_approved: bool

def validate_license(state: SoftwareState):
    state['validation_checks'].append('License verified')
    return {'validation_checks': state['validation_checks']}

def audit_content(state: SoftwareState):
    state['validation_checks'].append('Content accuracy confirmed')
    return {'validation_checks': state['validation_checks'], 'is_approved': True}

workflow = StateGraph(SoftwareState)
workflow.add_node('validate', validate_license)
workflow.add_node('audit', audit_content)
workflow.set_entry_point('validate')
workflow.add_edge('validate', 'audit')
workflow.add_edge('audit', END)
graph = workflow.compile()
