from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class PharmState(TypedDict):
    batch_id: str
    purity_level: float
    gmp_certified: bool
    approved: bool

def validate_purity(state: PharmState) -> PharmState:
    state['approved'] = state['purity_level'] >= 99.0 and state['gmp_certified']
    return state

def log_pharm_check(state: PharmState) -> PharmState:
    print(f'Batch {state['batch_id']} approval status: {state['approved']}')
    return state

graph = StateGraph(PharmState)
graph.add_node('validate', validate_purity)
graph.add_node('logging', log_pharm_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'logging')
graph.add_edge('logging', END)
graph = graph.compile()
