from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    product_id: str
    quality_docs: list
    is_approved: bool

def validate_gmp(state: ProcurementState):
    state['is_approved'] = all('gmp_cert' in doc for doc in state['quality_docs'])
    print('Validating GMP status...')
    return state

def check_temp_logs(state: ProcurementState):
    print('Verifying cold chain logs...')
    return state

graph = StateGraph(ProcurementState)
graph.add_node('validate_gmp', validate_gmp)
graph.add_node('check_temp_logs', check_temp_logs)
graph.add_edge('validate_gmp', 'check_temp_logs')
graph.add_edge('check_temp_logs', END)
graph.set_entry_point('validate_gmp')
graph = graph.compile()
