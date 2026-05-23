from typing import TypedDict
from langgraph.graph import StateGraph, END

class IUDState(TypedDict):
    device_id: str
    compliance_docs: dict
    is_approved: bool

def validate_compliance(state: IUDState) -> IUDState:
    required = ['iso_cert', 'regulatory_clearance']
    state['is_approved'] = all(k in state['compliance_docs'] for k in required)
    return state

def check_expiry(state: IUDState) -> IUDState:
    if state['is_approved']:
        print('Checking batch sterilization records...')
    return state

graph = StateGraph(IUDState)
graph.add_node('validate', validate_compliance)
graph.add_node('expiry_check', check_expiry)
graph.set_entry_point('validate')
graph.add_edge('validate', 'expiry_check')
graph.add_edge('expiry_check', END)
graph = graph.compile()
