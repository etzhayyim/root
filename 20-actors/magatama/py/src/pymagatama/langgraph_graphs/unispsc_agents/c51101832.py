from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    material_name: str
    quality_docs: List[str]
    storage_temp: float
    is_compliant: bool

def validate_gmp(state: ProcurementState):
    state['is_compliant'] = 'GMP Certification' in state['quality_docs']
    return state

def check_cold_chain(state: ProcurementState):
    if state['storage_temp'] > 25.0:
        state['is_compliant'] = False
    return state

graph = StateGraph(ProcurementState)
graph.add_node('validate_gmp', validate_gmp)
graph.add_node('check_cold_chain', check_cold_chain)
graph.set_entry_point('validate_gmp')
graph.add_edge('validate_gmp', 'check_cold_chain')
graph.add_edge('check_cold_chain', END)
graph = graph.compile()