from typing import TypedDict
from langgraph.graph import StateGraph, END

class PurificationState(TypedDict):
    sample_id: str
    purity_check_passed: bool
    storage_temp_valid: bool

def validate_sample_integrity(state: PurificationState) -> PurificationState:
    print(f'Validating viral DNA integrity for {state['sample_id']}')
    state['purity_check_passed'] = True
    return state

def check_cold_chain(state: PurificationState) -> PurificationState:
    print('Verifying cold chain logistics compliance')
    state['storage_temp_valid'] = True
    return state

graph = StateGraph(PurificationState)
graph.add_node('validate', validate_sample_integrity)
graph.add_node('cold_chain', check_cold_chain)
graph.set_entry_point('validate')
graph.add_edge('validate', 'cold_chain')
graph.add_edge('cold_chain', END)
app = graph.compile()
