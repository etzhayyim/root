from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    api_name: str
    purity_cert: bool
    compliance_check: bool
    status: str

def validate_compliance(state: ProcurementState):
    state['compliance_check'] = state['purity_cert'] and (state['api_name'] == 'Toltrazuril')
    state['status'] = 'COMPLIANT' if state['compliance_check'] else 'REJECTED'
    return state

builder = StateGraph(ProcurementState)
builder.add_node('validate', validate_compliance)
builder.set_entry_point('validate')
builder.add_edge('validate', END)
graph = builder.compile()
