from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    product: str
    compliance_cleared: bool
    temp_log_verified: bool

def validate_pharma(state: ProcurementState):
    print(f'Validating medical compliance for {state['product']}')
    return {'compliance_cleared': True}

def verify_cold_chain(state: ProcurementState):
    print('Checking cold chain logs for Methoxyflurane')
    return {'temp_log_verified': True}

graph = StateGraph(ProcurementState)
graph.add_node('validate_pharma', validate_pharma)
graph.add_node('verify_cold_chain', verify_cold_chain)
graph.set_entry_point('validate_pharma')
graph.add_edge('validate_pharma', 'verify_cold_chain')
graph.add_edge('verify_cold_chain', END)
app = graph.compile()