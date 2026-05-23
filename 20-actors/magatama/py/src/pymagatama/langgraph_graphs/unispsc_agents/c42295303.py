from typing import TypedDict
from langgraph.graph import StateGraph, END

class PerfusionState(TypedDict):
    part_number: str
    is_sterile: bool
    compliance_docs: list
    approval_status: str

def validate_certification(state: PerfusionState):
    state['approval_status'] = 'COMPLIANT' if 'ISO13485' in state['compliance_docs'] else 'REJECTED'
    return state

def check_sterility(state: PerfusionState):
    return {'is_sterile': True}

graph = StateGraph(PerfusionState)
graph.add_node('validate', validate_certification)
graph.add_node('sterility_check', check_sterility)
graph.set_entry_point('sterility_check')
graph.add_edge('sterility_check', 'validate')
graph.add_edge('validate', END)
graph = graph.compile()
