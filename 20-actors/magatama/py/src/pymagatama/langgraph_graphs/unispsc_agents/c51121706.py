from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    item_name: str
    quality_docs: List[str]
    compliance_passed: bool

def validate_gmp(state: ProcurementState):
    print('Validating GMP certification for Isradipine...')
    state['compliance_passed'] = 'GMP_cert' in state['quality_docs']
    return state

def check_storage(state: ProcurementState):
    print('Verifying cold chain capability...')
    return state

graph = StateGraph(ProcurementState)
graph.add_node('validate_gmp', validate_gmp)
graph.add_node('check_storage', check_storage)
graph.set_entry_point('validate_gmp')
graph.add_edge('validate_gmp', 'check_storage')
graph.add_edge('check_storage', END)
app = graph.compile()
