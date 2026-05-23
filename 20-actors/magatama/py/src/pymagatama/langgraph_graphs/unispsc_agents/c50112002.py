from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class MeatProcurementState(TypedDict):
    temp_log: List[float]
    safety_cert_valid: bool
    approved: bool

def validate_cold_chain(state: MeatProcurementState):
    # Ensure all temperature logs are below -18C
    state['approved'] = all(temp <= -18.0 for temp in state['temp_log'])
    return state

def check_certifications(state: MeatProcurementState):
    # Simulate HACCP and health cert verification
    state['approved'] = state['approved'] and state['safety_cert_valid']
    return state

graph = StateGraph(MeatProcurementState)
graph.add_node('validate_temp', validate_cold_chain)
graph.add_node('verify_certs', check_certifications)
graph.set_entry_point('validate_temp')
graph.add_edge('validate_temp', 'verify_certs')
graph.add_edge('verify_certs', END)
graph = graph.compile()
