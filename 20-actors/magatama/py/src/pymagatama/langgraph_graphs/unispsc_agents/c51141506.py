from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    purity_check: bool
    gmp_verified: bool
    temp_log_valid: bool

def validate_quality(state: ProcurementState):
    state['purity_check'] = True
    return 'check_gmp'

def check_gmp(state: ProcurementState):
    state['gmp_verified'] = True
    return 'verify_logistics'

def verify_logistics(state: ProcurementState):
    state['temp_log_valid'] = True
    return END

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_quality)
graph.add_node('check_gmp', check_gmp)
graph.add_node('verify_logistics', verify_logistics)
graph.set_entry_point('validate')
graph.add_edge('validate', 'check_gmp')
graph.add_edge('check_gmp', 'verify_logistics')
graph.add_edge('verify_logistics', END)
graph = graph.compile()