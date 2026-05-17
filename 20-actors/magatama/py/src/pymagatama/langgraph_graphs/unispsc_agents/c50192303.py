from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    temp_log_verified: bool
    haccp_compliant: bool
    quality_approved: bool

def validate_cold_chain(state: ProcurementState):
    state['temp_log_verified'] = True
    return 'Cold chain logs validated.'

def check_certification(state: ProcurementState):
    state['haccp_compliant'] = True
    return 'HACCP status confirmed.'

graph = StateGraph(ProcurementState)
graph.add_node('verify_log', validate_cold_chain)
graph.add_node('check_cert', check_certification)
graph.set_entry_point('verify_log')
graph.add_edge('verify_log', 'check_cert')
graph.add_edge('check_cert', END)
app = graph.compile()