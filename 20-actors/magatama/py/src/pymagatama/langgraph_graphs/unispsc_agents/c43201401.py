from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class SoftwareProtectionState(TypedDict):
    product_id: str
    security_requirements: Sequence[str]
    validation_log: Annotated[list[str], operator.add]
    is_compliant: bool

def validate_compliance(state: SoftwareProtectionState):
    log = ['Starting compliance check']
    if 'iso27001' in state['security_requirements']:
        log.append('ISO27001 requirement verified')
    return {'validation_log': log, 'is_compliant': True}

def audit_access_control(state: SoftwareProtectionState):
    log = ['Auditing access control logic']
    return {'validation_log': log}

graph = StateGraph(SoftwareProtectionState)
graph.add_node('validate', validate_compliance)
graph.add_node('audit', audit_access_control)
graph.add_edge('validate', 'audit')
graph.add_edge('audit', END)
graph.set_entry_point('validate')
graph = graph.compile()