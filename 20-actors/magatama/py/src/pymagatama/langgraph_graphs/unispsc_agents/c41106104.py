from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class AssayState(TypedDict):
    lot_number: str
    quality_status: str
    requires_cold_chain: bool

def validate_lot(state: AssayState):
    print(f'Validating lot: {state["lot_number"]}')
    return {'quality_status': 'verified'}

def check_temp(state: AssayState):
    print('Checking cold chain requirements...')
    return {'requires_cold_chain': True}

graph = StateGraph(AssayState)
graph.add_node('Validate', validate_lot)
graph.add_node('ColdChain', check_temp)
graph.add_edge('Validate', 'ColdChain')
graph.add_edge('ColdChain', END)
graph.set_entry_point('Validate')
graph = graph.compile()
