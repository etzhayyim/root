from langgraph.graph import StateGraph, END
from typing import TypedDict

class ProcurementState(TypedDict):
    drug_name: str
    compliance_check: bool
    temp_log_verified: bool

def validate_drug(state: ProcurementState):
    state['compliance_check'] = True if state['drug_name'] == 'Bupivacaine' else False
    return state

def verify_cold_chain(state: ProcurementState):
    state['temp_log_verified'] = True
    return state

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_drug)
graph.add_node('cold_chain', verify_cold_chain)
graph.set_entry_point('validate')
graph.add_edge('validate', 'cold_chain')
graph.add_edge('cold_chain', END)
graph = graph.compile()
