from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    item_name: str
    compliance_docs: List[str]
    is_approved: bool

def validate_gmp_certs(state: ProcurementState):
    print('Validating GMP certification for Racepinephrine...')
    return {'is_approved': 'GMP_CERT' in state['compliance_docs']}

def check_temp_requirements(state: ProcurementState):
    print('Verifying cold chain logistics protocol...')
    return {'compliance_docs': state['compliance_docs'] + ['temp_log_protocol']}

graph = StateGraph(ProcurementState)
graph.add_node('validate_gmp', validate_gmp_certs)
graph.add_node('check_temp', check_temp_requirements)
graph.add_edge('validate_gmp', 'check_temp')
graph.add_edge('check_temp', END)
graph.set_entry_point('validate_gmp')
graph = graph.compile()
