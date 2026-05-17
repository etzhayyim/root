from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    batch_id: str
    compliance_docs: list
    is_verified: bool

def validate_gmp(state: ProcurementState):
    print(f'Validating GMP for batch {state.batch_id}')
    return {'is_verified': True}

def check_stability(state: ProcurementState):
    print('Checking stability data...')
    return {'is_verified': state.is_verified and True}

graph = StateGraph(ProcurementState)
graph.add_node('validate_gmp', validate_gmp)
graph.add_node('check_stability', check_stability)
graph.add_edge('validate_gmp', 'check_stability')
graph.add_edge('check_stability', END)
graph.set_entry_point('validate_gmp')
compiled_graph = graph.compile()