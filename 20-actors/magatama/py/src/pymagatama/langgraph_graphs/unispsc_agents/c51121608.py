from typing import TypedDict
from langgraph.graph import StateGraph, END

class NicardipineState(TypedDict):
    batch_number: str
    purity_level: float
    qc_passed: bool

def validate_purity(state: NicardipineState):
    state['qc_passed'] = state['purity_level'] >= 99.5
    return 'validate_purity'

def check_cold_chain(state: NicardipineState):
    # Simulate cold chain validation
    return 'log_result'

graph = StateGraph(NicardipineState)
graph.add_node('validate', validate_purity)
graph.add_node('cold_chain', check_cold_chain)
graph.add_edge('validate', 'cold_chain')
graph.add_edge('cold_chain', END)
graph.set_entry_point('validate')