from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    batch_id: str
    purity_check: bool
    compliance_verified: bool
    storage_temp_verified: bool

def validate_gmp(state):
    print(f'Validating GMP for batch {state["batch_id"]}')
    return {'compliance_verified': True}

def check_temp(state):
    print('Verifying cold chain integrity')
    return {'storage_temp_verified': True}

graph = StateGraph(ProcurementState)
graph.add_node('gmp_check', validate_gmp)
graph.add_node('temp_check', check_temp)
graph.set_entry_point('gmp_check')
graph.add_edge('gmp_check', 'temp_check')
graph.add_edge('temp_check', END)
graph = graph.compile()