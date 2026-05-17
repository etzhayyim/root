from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    material_name: str
    quality_docs: list
    is_approved: bool

def validate_gmp_certs(state: ProcurementState):
    state['is_approved'] = 'GMP' in state['quality_docs']
    return state

def check_cold_chain(state: ProcurementState):
    print('Verifying temperature control for Arbutamine hydrochloride')
    return state

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_gmp_certs)
graph.add_node('cold_chain', check_cold_chain)
graph.set_entry_point('validate')
graph.add_edge('validate', 'cold_chain')
graph.add_edge('cold_chain', END)
graph = graph.compile()