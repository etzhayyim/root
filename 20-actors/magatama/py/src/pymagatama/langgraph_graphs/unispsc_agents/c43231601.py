from typing import TypedDict
from langgraph.graph import StateGraph, END

class AccountingSoftwareState(TypedDict):
    requirements: dict
    compliance_check: bool
    final_approval: bool

def validate_compliance(state: AccountingSoftwareState):
    compliance = state['requirements'].get('security_cert', False)
    return {'compliance_check': compliance}

def approve_procurement(state: AccountingSoftwareState):
    approval = state['compliance_check'] and state['requirements'].get('scope_match', False)
    return {'final_approval': approval}

graph = StateGraph(AccountingSoftwareState)
graph.add_node('compliance', validate_compliance)
graph.add_node('approval', approve_procurement)
graph.set_entry_point('compliance')
graph.add_edge('compliance', 'approval')
graph.add_edge('approval', END)
graph = graph.compile()