from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    drug_name: str
    temp_log: List[float]
    is_validated: bool

def validate_cold_chain(state: ProcurementState):
    is_valid = all(-2 <= t <= 8 for t in state['temp_log'])
    print(f'Validating cold chain: {is_valid}')
    return {'is_validated': is_valid}

def process_procurement(state: ProcurementState):
    return {'drug_name': state['drug_name']}

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_cold_chain)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()