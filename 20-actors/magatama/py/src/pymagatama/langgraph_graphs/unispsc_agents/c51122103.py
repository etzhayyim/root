from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    item_name: str
    purity: float
    gmp_verified: bool
    status: str

def validate_gmp(state: ProcurementState):
    print('Verifying GMP certification...')
    state['gmp_verified'] = True
    return state

def check_purity(state: ProcurementState):
    print(f'Checking purity level: {state['purity']}%')
    state['status'] = 'Validated' if state['purity'] >= 99.0 else 'Rejected'
    return state

graph = StateGraph(ProcurementState)
graph.add_node('validate_gmp', validate_gmp)
graph.add_node('check_purity', check_purity)
graph.set_entry_point('validate_gmp')
graph.add_edge('validate_gmp', 'check_purity')
graph.add_edge('check_purity', END)
graph = graph.compile()