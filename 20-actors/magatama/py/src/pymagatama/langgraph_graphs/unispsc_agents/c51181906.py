from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    batch_id: str
    temp_log: list
    gmp_verified: bool
    approved: bool

def validate_cold_chain(state: ProcurementState):
    state['approved'] = all(temp < 8.0 for temp in state['temp_log'])
    print(f'Cold chain status: {state['approved']}')
    return 'check_gmp'

def check_gmp_status(state: ProcurementState):
    state['approved'] = state['approved'] and state['gmp_verified']
    return END

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_cold_chain)
graph.add_node('check_gmp', check_gmp_status)
graph.set_entry_point('validate')
graph.add_edge('validate', 'check_gmp')
graph.add_edge('check_gmp', END)
app = graph.compile()