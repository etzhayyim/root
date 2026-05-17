from typing import TypedDict
from langgraph.graph import StateGraph, END

class PharmState(TypedDict):
    purity: float
    gmp_compliant: bool
    validation_status: str

def check_purity(state: PharmState):
    state['validation_status'] = 'PASSED' if state['purity'] >= 99.0 else 'FAILED'
    return state

def verify_gmp(state: PharmState):
    if not state.get('gmp_compliant', False):
        state['validation_status'] = 'REJECTED'
    return state

graph = StateGraph(PharmState)
graph.add_node('check_purity', check_purity)
graph.add_node('verify_gmp', verify_gmp)
graph.add_edge('check_purity', 'verify_gmp')
graph.add_edge('verify_gmp', END)
graph.set_entry_point('check_purity')
graph = graph.compile()