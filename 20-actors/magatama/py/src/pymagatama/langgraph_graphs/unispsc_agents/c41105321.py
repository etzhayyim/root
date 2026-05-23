from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ReagentState(TypedDict):
    product_id: str
    purity: float
    storage_temp: float
    qc_passed: bool

def validate_purity(state: ReagentState):
    state['qc_passed'] = state['purity'] >= 99.0
    return state

def check_cold_chain(state: ReagentState):
    if state['storage_temp'] > 8.0:
        state['qc_passed'] = False
    return state

graph = StateGraph(ReagentState)
graph.add_node('validate_purity', validate_purity)
graph.add_node('check_cold_chain', check_cold_chain)
graph.add_edge('validate_purity', 'check_cold_chain')
graph.add_edge('check_cold_chain', END)
graph.set_entry_point('validate_purity')
