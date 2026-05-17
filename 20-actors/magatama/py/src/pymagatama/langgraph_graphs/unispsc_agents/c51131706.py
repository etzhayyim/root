from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    product: str
    quality_docs: list
    shipping_temp: float
    approved: bool

def validate_gmp(state: ProcurementState):
    state['approved'] = 'GMP_Cert' in state['quality_docs']
    return state

def check_cold_chain(state: ProcurementState):
    state['approved'] = state['approved'] and (2.0 <= state['shipping_temp'] <= 8.0)
    return state

graph = StateGraph(ProcurementState)
graph.add_node('validate_gmp', validate_gmp)
graph.add_node('check_cold_chain', check_cold_chain)
graph.set_entry_point('validate_gmp')
graph.add_edge('validate_gmp', 'check_cold_chain')
graph.add_edge('check_cold_chain', END)
graph = graph.compile()