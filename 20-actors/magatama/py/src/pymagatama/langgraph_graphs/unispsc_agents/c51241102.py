from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class DrugProcurementState(TypedDict):
    batch_id: str
    purity_level: float
    temp_log: List[float]
    is_verified: bool

def validate_purity(state: DrugProcurementState):
    state['is_verified'] = state['purity_level'] >= 99.0
    return state

def check_cold_chain(state: DrugProcurementState):
    if any(t > 25.0 for t in state['temp_log']):
        state['is_verified'] = False
    return state

graph = StateGraph(DrugProcurementState)
graph.add_node('validate_purity', validate_purity)
graph.add_node('check_cold_chain', check_cold_chain)
graph.set_entry_point('validate_purity')
graph.add_edge('validate_purity', 'check_cold_chain')
graph.add_edge('check_cold_chain', END)
graph = graph.compile()
