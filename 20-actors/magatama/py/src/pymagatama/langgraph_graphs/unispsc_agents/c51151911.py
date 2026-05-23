from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    product: str
    temp_log: list
    validation_status: bool

def validate_cold_chain(state: ProcurementState):
    # Simulate cold chain validation for Suxamethonium
    state['validation_status'] = all(t <= 8.0 for t in state['temp_log'])
    print(f'Validation result: {state['validation_status']}')
    return 'end'

def create_graph():
    graph = StateGraph(ProcurementState)
    graph.add_node('validate', validate_cold_chain)
    graph.set_entry_point('validate')
    graph.add_edge('validate', END)
    return graph.compile()

graph = create_graph()
