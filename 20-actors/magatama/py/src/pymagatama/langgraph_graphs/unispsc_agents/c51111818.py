from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class ProcurementState(TypedDict):
    drug_batch_id: str
    quality_docs: List[str]
    temp_log_verified: bool
    is_approved: bool

def validate_gmp(state: ProcurementState):
    state['quality_docs'].append('GMP_CERT_VALIDATED')
    return state

def check_temp_logs(state: ProcurementState):
    state['temp_log_verified'] = True
    return state

def finalize_procurement(state: ProcurementState):
    state['is_approved'] = True
    return state

graph = StateGraph(ProcurementState)
graph.add_node('validate_gmp', validate_gmp)
graph.add_node('check_temp_logs', check_temp_logs)
graph.add_node('finalize', finalize_procurement)
graph.add_edge('validate_gmp', 'check_temp_logs')
graph.add_edge('check_temp_logs', 'finalize')
graph.add_edge('finalize', END)
graph.set_entry_point('validate_gmp')
compiled_graph = graph.compile()